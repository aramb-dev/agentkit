import sys
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

# Configuration from environment variables
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
CONVERSATION_HISTORY_LIMIT = int(os.getenv("CONVERSATION_HISTORY_LIMIT", "50"))  # 50 messages default

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
):
    """
    Send a chat message to AgentKit with optional file attachments and conversation history.
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
                        detail=f"File '{file.filename}' is too large. Maximum size allowed: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
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
        message_with_files, model, conversation_history
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


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
