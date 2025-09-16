from typing import Dict, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from .prompts import AGENT_PROMPT
from .tools import web_search_tool, retriever_tool, memory_tool


async def run_agent(query: str, model: str) -> Dict[str, Optional[str]]:
    """
    Runs the agent loop.
    """
    if model == "phi3":
        llm = OllamaLLM(model="phi3")
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")  # type: ignore

    tools = [web_search_tool, retriever_tool, memory_tool]  # type: ignore

    agent = create_react_agent(llm, tools, AGENT_PROMPT)  # type: ignore
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True, handle_parsing_errors=True
    )

    response = await agent_executor.ainvoke({"input": query})

    return {"answer": response.get("output"), "tool_used": "agent"}
