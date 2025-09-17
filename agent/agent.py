"""Agent orchestration entrypoints."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List

from .prompts import AVAILABLE_TOOLS_PROMPT, SUMMARY_PROMPT, SYSTEM_PROMPT
from .router import describe_tools, select_tool
from .tools import TOOLS
from .llm_client import llm_client


@dataclass
class Message:
    role: str
    content: str


async def _format_response(
    message: str, model: str, tool_name: str, tool_output: str
) -> str:
    """Create the final response string sent back to the caller using LLM."""

    if tool_name == "idle":
        # For idle responses, use LLM to generate contextual responses
        prompt = f"""You are AgentKit, a helpful modular AI agent. The user said: "{message}"

Respond naturally and helpfully. You have access to these capabilities:
- Web search (when users ask to search, find, or lookup information)
- Document explanations (when users ask about architecture, documentation, or explanations)
- Memory functions (when users ask you to remember or recall something)

If this is a greeting, be friendly and explain your capabilities.
If this is a general question, try to be helpful while mentioning your available tools.
Keep your response concise and actionable."""

        return await llm_client.generate_response(prompt, model)
    else:
        # For tool-specific responses, use LLM to interpret and present tool output
        prompt = f"""You are AgentKit, a helpful AI agent. The user asked: "{message}"

I used the {tool_name} tool and got this result: {tool_output}

Please provide a helpful, natural response to the user based on this information.
Be conversational and format the information clearly."""

        return await llm_client.generate_response(prompt, model)


def _summarise(history: List[Message], final_answer: str) -> str:
    conversation = "\n".join(f"{msg.role}: {msg.content}" for msg in history)
    conversation += f"\nagent: {final_answer}"
    return SUMMARY_PROMPT.format(conversation=conversation)


async def run_agent(message: str, model: str) -> Dict[str, str]:
    """Entry point used by the FastAPI app."""

    history = [Message(role="user", content=message)]
    tool_name = select_tool(message)
    tool = TOOLS[tool_name]
    tool_output = await tool.run(message)

    if tool_name != "idle" and tool_output:
        history.append(Message(role="tool", content=f"{tool_name}: {tool_output}"))

    final_answer = await _format_response(message, model, tool_name, tool_output)
    summary = _summarise(history, final_answer)

    tool_overview = AVAILABLE_TOOLS_PROMPT.format(tool_overview=describe_tools())

    return {
        "answer": final_answer,
        "tool_used": tool_name,
        "tool_output": tool_output,
        "model": model,
        "context": tool_overview,
        "summary": summary,
    }
