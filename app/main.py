import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add the parent directory to Python path so we can import the agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
from agent.agent import run_agent

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    model: str


@app.post("/chat")
async def chat(request: ChatRequest):
    response = await run_agent(request.message, request.model)
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
