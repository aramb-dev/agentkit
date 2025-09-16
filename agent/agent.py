from typing import Dict, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.llms import Ollama
from .prompts import AGENT_PROMPT
from .tools import web_search_tool, retriever_tool, memory_tool


async def run_agent(query: str) -> Dict[str, Optional[str]]:
    """
    Runs the agent loop.
    """
    llm = Ollama(model="phi3")
    tools = [web_search_tool, retriever_tool, memory_tool]

    agent = create_react_agent(llm, tools, AGENT_PROMPT)  # type: ignore
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    response = await agent_executor.ainvoke({"input": query})

    return {"answer": response.get("output"), "tool_used": "agent"}
