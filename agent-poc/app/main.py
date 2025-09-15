import sys
import os

# Add the parent directory to the Python path to allow for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from pydantic import BaseModel
from agent.agent import run_agent

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
    response = run_agent(request.message)
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
