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
from agent.agent import run_agent
from agent.llm_client import llm_client

app = FastAPI(title="AgentKit Chat API", version="1.0.0")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    model: str


class ModelResponse(BaseModel):
    available_models: List[str]
    default_model: str


@app.post("/chat")
async def chat(
    message: str = Form(...),
    model: str = Form(...),
    files: List[UploadFile] = File(default=[]),
):
    """
    Send a chat message to AgentKit with optional file attachments.
    """
    # Process uploaded files if any
    file_contents = []
    if files and files[0].filename:  # Check if files were actually uploaded
        for file in files:
            if file.filename:
                content = await file.read()
                file_contents.append(
                    {
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": len(content),
                        "content": (
                            content.decode("utf-8", errors="ignore")
                            if file.content_type.startswith("text/")
                            else None
                        ),
                    }
                )

    # For now, append file info to message if files were uploaded
    if file_contents:
        file_info = "\n\nAttached files:\n" + "\n".join(
            [f"- {f['filename']} ({f['size']} bytes)" for f in file_contents]
        )
        message_with_files = message + file_info
    else:
        message_with_files = message

    response = await run_agent(message_with_files, model)
    return response


@app.get("/models", response_model=ModelResponse)
async def get_models():
    """
    Get available AI models and the default model.
    """
    available_models = llm_client.get_available_models()
    default_model = llm_client.get_default_model()

    return ModelResponse(available_models=available_models, default_model=default_model)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
