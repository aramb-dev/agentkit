from typing import Dict, Optional
import os
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
        # Check if Google API key is available
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            return {
                "answer": "Error: Google API key not found. Please set GOOGLE_API_KEY in your .env file to use Gemini models.",
                "tool_used": None
            }
        
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",  # Use available model
                google_api_key=google_api_key
            )
        except Exception as e:
            return {
                "answer": f"Error initializing Gemini model: {str(e)}",
                "tool_used": None
            }

    tools = [web_search_tool, retriever_tool, memory_tool]  # type: ignore

    agent = create_react_agent(llm, tools, AGENT_PROMPT)  # type: ignore
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    response = await agent_executor.ainvoke({"input": query})

    tool_used = None
    if "intermediate_steps" in response and response["intermediate_steps"]:
        tool_used = response["intermediate_steps"][0][0].tool

    return {"answer": response.get("output"), "tool_used": tool_used}
