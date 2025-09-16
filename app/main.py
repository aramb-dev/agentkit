from fastapi import FastAPI
from pydantic import BaseModel
from agent.agent import run_agent

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    response = await run_agent(request.message)
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
