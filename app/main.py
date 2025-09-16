from fastapi import FastAPI
from pydantic import BaseModel
from agent.agent import run_agent
from dotenv import load_dotenv

load_dotenv()

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
