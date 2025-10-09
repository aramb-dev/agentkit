import sys
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

# Configuration from environment variables
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB default
CONVERSATION_HISTORY_LIMIT = int(
    os.getenv("CONVERSATION_HISTORY_LIMIT", "50")
)  # 50 messages default
ENABLE_RETRY_LOGIC = os.getenv("ENABLE_RETRY_LOGIC", "true").lower() == "true"
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "1"))

# Add the parent directory to Python path so we can import the agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from agent.agent import run_agent_with_history
from agent.llm_client import llm_client
from agent.document_processor import DocumentProcessor
from agent.file_manager import file_manager
import uuid
import tempfile
import logging
import traceback
from datetime import datetime
from rag.ingest import build_doc_chunks
from rag.store import upsert_chunks, list_collections, delete_namespace, get_collection, delete_document

# Configure logging for error tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AgentKit Chat API", version="1.0.0")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for standardized error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized error format."""
    error_code = ErrorCodes.INTERNAL_ERROR
    retry_after = None
    
    # Map HTTP status codes to error codes
    if exc.status_code == 413:
        error_code = ErrorCodes.FILE_TOO_LARGE
    elif exc.status_code == 400:
        error_code = ErrorCodes.VALIDATION_ERROR
    elif exc.status_code == 404:
        error_code = ErrorCodes.NOT_FOUND
    elif exc.status_code == 409:
        error_code = ErrorCodes.CONFLICT
    elif exc.status_code == 429:
        error_code = ErrorCodes.RATE_LIMIT_EXCEEDED
        retry_after = 60
    elif exc.status_code >= 500:
        error_code = ErrorCodes.INTERNAL_ERROR
    
    # Log the error
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=error_code,
            message=str(exc.detail),
            details={"status_code": exc.status_code, "path": str(request.url.path)},
            retry_after=retry_after
        ),
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with standardized error format."""
    # Log the full error with traceback
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCodes.INTERNAL_ERROR,
            message="An unexpected error occurred. Please try again later.",
            details={
                "error_type": type(exc).__name__,
                "path": str(request.url.path)
            } if os.getenv("DEBUG") else None
        ),
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


# Request validation middleware
@app.middleware("http")
async def validate_request_middleware(request: Request, call_next):
    """Add request ID and perform basic validation."""
    # Add unique request ID for tracing
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Log incoming request
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        logger.error(f"Request {request_id} failed: {str(e)}")
        raise


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


class ErrorDetail(BaseModel):
    """Standardized error detail structure."""
    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    success: bool = False
    error: ErrorDetail
    request_id: Optional[str] = None


class ValidationError(BaseModel):
    """Validation error details."""
    field: str
    message: str
    value: Optional[Any] = None


# Error code constants
class ErrorCodes:
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"


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

                # Validate file with comprehensive checks
                try:
                    validation_result = validate_file_upload(file, content)
                    logger.info(f"Chat file validated: {validation_result['filename']}")
                except HTTPException as e:
                    logger.error(f"Chat file validation failed: {e.detail}")
                    raise

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


# File validation constants
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md', '.markdown', '.json']
SUPPORTED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'text/markdown': '.md',
    'application/json': '.json'
}


def validate_file_upload(file: UploadFile, content: bytes) -> Dict[str, Any]:
    """
    Validate file upload with comprehensive checks.
    
    Returns validation result with details.
    Raises HTTPException if validation fails.
    """
    errors = []
    
    # Check if filename exists
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )
    
    # Check for potentially malicious filenames (BEFORE extension check)
    if '..' in file.filename or '/' in file.filename or '\\' in file.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename: path traversal detected"
        )
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    # Validate MIME type
    if file.content_type and file.content_type not in SUPPORTED_MIME_TYPES:
        logger.warning(f"Unexpected MIME type: {file.content_type} for file: {file.filename}")
    
    # Check file size
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size / (1024*1024):.2f}MB). Maximum size: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )
    
    return {
        "valid": True,
        "filename": file.filename,
        "size": file_size,
        "extension": file_ext,
        "mime_type": file.content_type
    }


@app.post("/docs/ingest")
async def ingest_doc(
    file: UploadFile = File(...),
    namespace: str = Form("default"),
    session_id: str = Form("default"),
):
    """
    Ingest a document into the vector store for RAG retrieval.

    This endpoint processes uploaded files (PDF, DOCX, TXT, MD, JSON) by:
    1. Validating file type and size
    2. Extracting text content
    3. Chunking the text into searchable segments
    4. Generating embeddings and storing in vector database
    5. Associating chunks with namespace for isolation
    
    Supported formats: PDF, DOCX, TXT, MD, JSON
    Max file size: 50MB
    """
    # Read file content
    content = await file.read()
    
    # Comprehensive file validation
    try:
        validation_result = validate_file_upload(file, content)
        logger.info(f"File validation passed: {validation_result['filename']} ({validation_result['size']} bytes)")
    except HTTPException as e:
        logger.warning(f"File validation failed: {e.detail}")
        raise

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


@app.get("/monitoring/rag")
def get_rag_performance():
    """Get RAG system performance metrics and configuration."""
    from rag.store import get_performance_stats, get_cache_stats
    
    return {
        "rag_performance": get_performance_stats(),
        "timestamp": _get_current_timestamp()
    }


@app.post("/monitoring/rag/cache/clear")
def clear_rag_cache():
    """Clear RAG query cache."""
    from rag.store import clear_cache
    
    clear_cache()
    return {
        "message": "RAG cache cleared successfully",
        "timestamp": _get_current_timestamp()
    }


@app.post("/monitoring/reset")
def reset_performance_metrics():
    """Reset all performance metrics (useful for testing)."""
    from agent.router import reset_routing_metrics
    from agent.tools import reset_tool_metrics
    from rag.store import clear_cache
    
    reset_routing_metrics()
    reset_tool_metrics()
    clear_cache()
    
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
    from rag.store import get_config as get_rag_config
    
    rag_config = get_rag_config()
    
    return {
        "status": "operational",
        "version": "1.0.0",
        "configuration": {
            "max_file_size_mb": round(MAX_FILE_SIZE / (1024 * 1024), 1),
            "conversation_history_limit": CONVERSATION_HISTORY_LIMIT,
            "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
            "tavily_api_configured": bool(os.getenv("TAVILY_API_KEY")),
            "rag_config": {
                "embedding_model": rag_config.get("embedding_model"),
                "default_k": rag_config.get("default_k"),
                "cache_enabled": rag_config.get("cache_enabled")
            }
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
            "monitoring": "/monitoring/rag",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
