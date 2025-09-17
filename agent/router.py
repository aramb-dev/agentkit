"""Routing logic for choosing tools inside AgentKit."""

from __future__ import annotations

from typing import Optional
from .tools import TOOLS
from .llm_client import llm_client


async def select_tool(message: str) -> str:
    """Choose the most appropriate tool using LLM-based intelligent routing."""
    
    # Create a prompt for the LLM to choose the best tool
    tool_descriptions = "\n".join([
        f"- {name}: {tool.description}" 
        for name, tool in TOOLS.items()
    ])
    
    routing_prompt = f"""You are a smart routing agent for AgentKit. Your job is to analyze the user's query and select the most appropriate tool.

Available tools:
{tool_descriptions}

User query: "{message}"

Rules for tool selection:
- Use "web" for: factual questions, current events, news, research, "who/what/when/where" questions, company information, relationships between entities, anything requiring up-to-date information
- Use "rag" for: questions about AgentKit itself, architecture, setup, documentation, how AgentKit works
- Use "memory" for: requests to remember/store information or recall previously stored information
- Use "idle" for: greetings, general conversation, thanks, or when no specific tool is needed

Respond with ONLY the tool name (web, rag, memory, or idle). No explanation needed."""

    try:
        # Use LLM to intelligently select the tool
        llm_response = await llm_client.generate_response(routing_prompt, "gemini")
        selected_tool = llm_response.strip().lower()
        
        # Validate the response and ensure it's a valid tool
        if selected_tool in TOOLS:
            return selected_tool
        else:
            # Fallback to keyword-based routing if LLM returns invalid response
            return _fallback_keyword_routing(message)
            
    except Exception as e:
        print(f"Error in LLM routing: {e}")
        return _fallback_keyword_routing(message)


def _fallback_keyword_routing(message: str) -> str:
    """Fallback keyword-based routing when LLM routing fails."""
    lowered = message.lower()
    
    # Simple keyword matching as fallback
    if any(word in lowered for word in ["search", "find", "who", "what", "when", "where", "news", "latest"]):
        return "web"
    elif any(word in lowered for word in ["architecture", "setup", "explain agentkit", "how does agentkit"]):
        return "rag"
    elif any(word in lowered for word in ["remember", "recall", "store", "memory"]):
        return "memory"
    else:
        return "idle"


def describe_tools() -> str:
    """Return a human readable list of available tools."""

    lines = [f"- {tool.name}: {tool.description}" for tool in TOOLS.values()]
    return "\n".join(lines)
