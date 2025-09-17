import sys
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

# Add the parent directory to Python path so we can import the agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agent.agent import run_agent_with_history
from agent.llm_client import llm_client
from agent.document_processor import DocumentProcessor

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
    except json.JSONDecodeError:
        conversation_history = []

    # Process uploaded files if any
    processed_files = []
    if files and files[0].filename:  # Check if files were actually uploaded
        for file in files:
            if file.filename:
                content = await file.read()

                # Use enhanced document processor
                file_result = await DocumentProcessor.process_file(
                    content,
                    file.filename,
                    file.content_type or "application/octet-stream",
                )
                processed_files.append(file_result)

    # Create document summary for the agent
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
    return response


@app.get("/models", response_model=ModelResponse)
async def get_models():
    """
    Get available AI models and the default model.
    """
    available_models = llm_client.get_available_models()
    default_model = llm_client.get_default_model()

    return ModelResponse(available_models=available_models, default_model=default_model)


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
