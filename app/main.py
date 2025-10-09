import sys
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

# Configuration from environment variables
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
CONVERSATION_HISTORY_LIMIT = int(
    os.getenv("CONVERSATION_HISTORY_LIMIT", "50")
)  # 50 messages default

# Add the parent directory to Python path so we can import the agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agent.agent import run_agent_with_history
from agent.llm_client import llm_client
from agent.document_processor import DocumentProcessor
from agent.file_manager import file_manager
import uuid
import tempfile
from rag.ingest import build_doc_chunks
from rag.store import upsert_chunks, list_collections, delete_namespace, get_collection, delete_document

app = FastAPI(title="AgentKit Chat API", version="1.0.0")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    model: str
    history: Optional[List[ChatMessage]] = []


class ModelResponse(BaseModel):
    available_models: List[str]
    default_model: str


@app.post("/chat")
async def chat(
    message: str = Form(...),
    model: str = Form(...),
    history: str = Form(default="[]"),  # JSON string of message history
    files: List[UploadFile] = File(default=[]),
    namespace: str = Form(default="default"),  # RAG namespace for document isolation
    session_id: str = Form(default="default"),  # Session ID for conversation context
    search_mode: str = Form(default="auto"),  # Search mode: auto, web, documents, hybrid
):
    """
    Send a chat message to AgentKit with optional file attachments and conversation history.
    Supports RAG retrieval from previously ingested documents using namespace isolation.
    Advanced search modes: auto (intelligent selection), web, documents, or hybrid (both).
    """
    import json

    # Parse conversation history
    try:
        conversation_history = json.loads(history) if history != "[]" else []
        # Limit conversation history to prevent memory issues
        if len(conversation_history) > CONVERSATION_HISTORY_LIMIT:
            conversation_history = conversation_history[-CONVERSATION_HISTORY_LIMIT:]
    except json.JSONDecodeError:
        conversation_history = []

    # Process uploaded files if any
    processed_files = []
    stored_files = []

    if files and files[0].filename:  # Check if files were actually uploaded
        for file in files:
            if file.filename:
                content = await file.read()

                # Check file size limit
                if len(content) > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File '{file.filename}' is too large. Maximum size allowed: {MAX_FILE_SIZE / (1024*1024):.1f}MB",
                    )

                # Store file permanently
                file_metadata = await file_manager.store_file(
                    content,
                    file.filename,
                    file.content_type or "application/octet-stream",
                    user_id="default",  # TODO: Add proper user management
                )
                stored_files.append(file_metadata)

                # Process file content for immediate use
                file_result = await DocumentProcessor.process_file(
                    content,
                    file.filename,
                    file.content_type or "application/octet-stream",
                )
                file_result["file_id"] = file_metadata["file_id"]  # Link to stored file
                processed_files.append(
                    file_result
                )  # Create document summary for the agent
    document_summary = DocumentProcessor.create_document_summary(processed_files)

    # Combine user message with document content
    if document_summary:
        message_with_files = f"{message}\n\n{document_summary}"

        # Add full document content for analysis
        for file_info in processed_files:
            if file_info["processing_success"] and file_info["text_content"]:
                message_with_files += (
                    f"\n\n--- Content of {file_info['filename']} ---\n"
                )
                message_with_files += file_info["text_content"][
                    :5000
                ]  # Limit to 5K chars per file
                if len(file_info["text_content"]) > 5000:
                    message_with_files += "\n[Content truncated...]"
    else:
        message_with_files = message

    response = await run_agent_with_history(
        message_with_files, model, conversation_history, namespace, session_id, search_mode
    )

    # Add stored file information to response
    if stored_files:
        response["stored_files"] = [
            {
                "file_id": f["file_id"],
                "original_filename": f["original_filename"],
                "file_size": f["file_size"],
                "content_type": f["content_type"],
            }
            for f in stored_files
        ]

    return response


@app.get("/models", response_model=ModelResponse)
async def get_models():
    """
    Get available AI models and the default model.
    """
    available_models = llm_client.get_available_models()
    default_model = llm_client.get_default_model()

    return ModelResponse(available_models=available_models, default_model=default_model)


@app.post("/docs/ingest")
async def ingest_doc(
    file: UploadFile = File(...),
    namespace: str = Form("default"),
    session_id: str = Form("default"),
):
    """
    Ingest a document into the vector store for RAG retrieval.

    This endpoint processes uploaded files (PDF, DOCX, TXT, MD) by:
    1. Extracting text content
    2. Chunking the text into searchable segments
    3. Generating embeddings and storing in vector database
    4. Associating chunks with namespace for isolation
    
    Supported formats: PDF, DOCX, TXT, MD
    """
    # Validate file type
    SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md', '.markdown']
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )
    
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB",
        )

    # Save temporary file for processing
    file_ext = os.path.splitext(file.filename.lower())[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Build document chunks with metadata
        chunks = build_doc_chunks(
            tmp_path,
            metadata={
                "filename": file.filename,
                "namespace": namespace,
                "session_id": session_id,
                "doc_id": str(uuid.uuid4()),
            },
        )

        # Store chunks in vector database
        upsert_chunks(namespace, chunks)

        return {
            "status": "success",
            "message": "Document ingested successfully",
            "chunks": len(chunks),
            "namespace": namespace,
            "filename": file.filename,
            "doc_id": chunks[0]["metadata"]["doc_id"] if chunks else None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process document: {str(e)}"
        )

    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except:
            pass


@app.get("/files")
async def list_files(user_id: Optional[str] = None):
    """List all uploaded files."""
    files = file_manager.list_user_files(user_id)
    return {"files": files, "total": len(files)}


@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Get information about a specific file."""
    metadata = file_manager.get_file_metadata(file_id)
    if not metadata:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="File not found")
    return metadata


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a specific file."""
    success = file_manager.delete_file(file_id)
    if not success:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404, detail="File not found or could not be deleted"
        )
    return {"message": "File deleted successfully"}


@app.get("/storage/stats")
async def get_storage_stats():
    """Get storage usage statistics."""
    stats = file_manager.get_storage_stats()
    return stats


@app.post("/storage/cleanup")
async def cleanup_old_files(days_old: int = 30):
    """Clean up files older than specified days."""
    deleted_count = file_manager.cleanup_old_files(days_old)
    return {"message": f"Deleted {deleted_count} old files"}


@app.get("/file-support")
async def get_file_support():
    """
    Get information about supported file types and missing dependencies.
    """
    return {
        "supported_formats": DocumentProcessor.SUPPORTED_FORMATS,
        "missing_dependencies": DocumentProcessor.get_missing_dependencies(),
        "recommendations": {
            "pdf": (
                "pip install PyPDF2"
                if "PyPDF2" in DocumentProcessor.get_missing_dependencies()
                else "✅ Available"
            ),
            "docx": (
                "pip install python-docx"
                if "python-docx" in DocumentProcessor.get_missing_dependencies()
                else "✅ Available"
            ),
        },
    }


# Namespace Management Endpoints

@app.get("/namespaces")
async def list_namespaces():
    """List all available namespaces/collections."""
    try:
        namespaces = list_collections()
        # Always include 'default' namespace even if no documents are in it
        if "default" not in namespaces:
            namespaces.append("default")
        
        # Get document count for each namespace
        namespace_info = []
        for namespace in sorted(namespaces):
            try:
                collection = get_collection(namespace)
                count = collection.count()
                namespace_info.append({
                    "name": namespace,
                    "document_count": count,
                    "is_default": namespace == "default"
                })
            except Exception as e:
                print(f"Error getting count for namespace {namespace}: {e}")
                namespace_info.append({
                    "name": namespace,
                    "document_count": 0,
                    "is_default": namespace == "default"
                })
        
        return {
            "namespaces": namespace_info,
            "total": len(namespace_info)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list namespaces: {str(e)}"
        )


@app.post("/namespaces")
async def create_namespace(name: str = Form(...)):
    """Create a new namespace."""
    # Validate namespace name
    if not name or not name.strip():
        raise HTTPException(
            status_code=400, detail="Namespace name cannot be empty"
        )
    
    name = name.strip()
    
    # Check for invalid characters
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise HTTPException(
            status_code=400, 
            detail="Namespace name can only contain letters, numbers, underscores, and hyphens"
        )
    
    # Check if namespace already exists
    existing_namespaces = list_collections()
    if name in existing_namespaces:
        raise HTTPException(
            status_code=409, detail=f"Namespace '{name}' already exists"
        )
    
    try:
        # Create the namespace by getting a collection (this creates it)
        get_collection(name)
        return {
            "status": "success",
            "message": f"Namespace '{name}' created successfully",
            "namespace": name
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create namespace: {str(e)}"
        )


@app.delete("/namespaces/{namespace_name}")
async def delete_namespace_endpoint(namespace_name: str):
    """Delete a namespace and all its documents."""
    # Prevent deletion of default namespace
    if namespace_name == "default":
        raise HTTPException(
            status_code=400, detail="Cannot delete the default namespace"
        )
    
    # Check if namespace exists
    existing_namespaces = list_collections()
    if namespace_name not in existing_namespaces:
        raise HTTPException(
            status_code=404, detail=f"Namespace '{namespace_name}' not found"
        )
    
    try:
        delete_namespace(namespace_name)
        return {
            "status": "success",
            "message": f"Namespace '{namespace_name}' deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete namespace: {str(e)}"
        )


@app.put("/namespaces/{old_name}/rename")
async def rename_namespace(old_name: str, new_name: str = Form(...)):
    """Rename a namespace."""
    # Validate new namespace name
    if not new_name or not new_name.strip():
        raise HTTPException(
            status_code=400, detail="New namespace name cannot be empty"
        )
    
    new_name = new_name.strip()
    
    # Check for invalid characters
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', new_name):
        raise HTTPException(
            status_code=400, 
            detail="Namespace name can only contain letters, numbers, underscores, and hyphens"
        )
    
    # Prevent renaming default namespace
    if old_name == "default":
        raise HTTPException(
            status_code=400, detail="Cannot rename the default namespace"
        )
    
    # Check if old namespace exists
    existing_namespaces = list_collections()
    if old_name not in existing_namespaces:
        raise HTTPException(
            status_code=404, detail=f"Namespace '{old_name}' not found"
        )
    
    # Check if new name already exists
    if new_name in existing_namespaces:
        raise HTTPException(
            status_code=409, detail=f"Namespace '{new_name}' already exists"
        )
    
    try:
        # ChromaDB doesn't support renaming collections directly
        # We need to copy all documents to new collection and delete old one
        from rag.store import query
        
        # Get all documents from old namespace
        old_collection = get_collection(old_name)
        all_docs = old_collection.get()
        
        if all_docs["ids"]:
            # Create new collection and add all documents
            new_collection = get_collection(new_name)
            new_collection.upsert(
                ids=all_docs["ids"],
                embeddings=all_docs["embeddings"],
                metadatas=all_docs["metadatas"],
                documents=all_docs["documents"]
            )
        
        # Delete old namespace
        delete_namespace(old_name)
        
        return {
            "status": "success",
            "message": f"Namespace renamed from '{old_name}' to '{new_name}'",
            "old_name": old_name,
            "new_name": new_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to rename namespace: {str(e)}"
        )


@app.get("/namespaces/{namespace_name}/documents")
async def list_namespace_documents(namespace_name: str):
    """List all documents in a specific namespace."""
    # Check if namespace exists
    existing_namespaces = list_collections()
    if namespace_name not in existing_namespaces and namespace_name != "default":
        raise HTTPException(
            status_code=404, detail=f"Namespace '{namespace_name}' not found"
        )
    
    try:
        collection = get_collection(namespace_name)
        all_docs = collection.get()
        
        # Group documents by doc_id and extract metadata
        documents = {}
        for i, metadata in enumerate(all_docs.get("metadatas", [])):
            doc_id = metadata.get("doc_id")
            filename = metadata.get("filename")
            
            if doc_id and filename:
                if doc_id not in documents:
                    documents[doc_id] = {
                        "doc_id": doc_id,
                        "filename": filename,
                        "namespace": namespace_name,
                        "chunk_count": 0,
                        "session_id": metadata.get("session_id", "unknown")
                    }
                documents[doc_id]["chunk_count"] += 1
        
        document_list = list(documents.values())
        
        return {
            "namespace": namespace_name,
            "documents": document_list,
            "total_documents": len(document_list),
            "total_chunks": len(all_docs.get("ids", []))
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list documents in namespace: {str(e)}"
        )


@app.delete("/namespaces/{namespace_name}/documents/{doc_id}")
async def delete_document_endpoint(namespace_name: str, doc_id: str):
    """Delete a specific document from a namespace."""
    # Check if namespace exists
    existing_namespaces = list_collections()
    if namespace_name not in existing_namespaces and namespace_name != "default":
        raise HTTPException(
            status_code=404, detail=f"Namespace '{namespace_name}' not found"
        )
    
    try:
        deleted_chunks = delete_document(namespace_name, doc_id)
        
        if deleted_chunks == 0:
            raise HTTPException(
                status_code=404, detail=f"Document '{doc_id}' not found in namespace '{namespace_name}'"
            )
        
        return {
            "status": "success",
            "message": f"Document deleted successfully",
            "namespace": namespace_name,
            "doc_id": doc_id,
            "deleted_chunks": deleted_chunks
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete document: {str(e)}"
        )


@app.get("/monitoring/routing")
def get_routing_metrics():
    """Get routing system performance metrics."""
    from agent.router import get_routing_metrics
    return {
        "routing_metrics": get_routing_metrics(),
        "timestamp": _get_current_timestamp()
    }


@app.get("/monitoring/tools")  
def get_tool_performance():
    """Get tool performance metrics and statistics."""
    from agent.tools import get_all_tool_performance_stats
    return {
        "tool_performance": get_all_tool_performance_stats(),
        "timestamp": _get_current_timestamp()
    }


@app.get("/monitoring/system")
async def get_system_performance():
    """Get comprehensive system performance metrics."""
    from agent.router import get_routing_metrics
    from agent.tools import get_all_tool_performance_stats
    
    return {
        "routing_metrics": get_routing_metrics(), 
        "tool_performance": get_all_tool_performance_stats(),
        "llm_status": {
            "available_models": llm_client.get_available_models(),
            "default_model": llm_client.get_default_model(),
            "gemini_available": llm_client.is_available("gemini")
        },
        "timestamp": _get_current_timestamp()
    }


@app.post("/monitoring/reset")
def reset_performance_metrics():
    """Reset all performance metrics (useful for testing)."""
    from agent.router import reset_routing_metrics
    from agent.tools import reset_tool_metrics
    
    reset_routing_metrics()
    reset_tool_metrics()
    
    return {
        "message": "Performance metrics reset successfully",
        "timestamp": _get_current_timestamp()
    }


def _get_current_timestamp():
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/status")
async def get_system_status():
    """
    Get comprehensive system status including configuration and capabilities.
    """
    return {
        "status": "operational",
        "version": "1.0.0",
        "configuration": {
            "max_file_size_mb": round(MAX_FILE_SIZE / (1024 * 1024), 1),
            "conversation_history_limit": CONVERSATION_HISTORY_LIMIT,
            "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
            "tavily_api_configured": bool(os.getenv("TAVILY_API_KEY")),
        },
        "capabilities": {
            "ai_models": len(llm_client.get_available_models()),
            "supported_file_formats": list(DocumentProcessor.SUPPORTED_FORMATS.keys()),
            "missing_dependencies": DocumentProcessor.get_missing_dependencies(),
        },
        "endpoints": {
            "chat": "/chat",
            "upload": "/chat (with files)",
            "models": "/models",
            "files": "/files",
            "health": "/healthz",
            "api_docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
