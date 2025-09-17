"""Agent orchestration entrypoints."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List

from .prompts import AVAILABLE_TOOLS_PROMPT, SUMMARY_PROMPT, SYSTEM_PROMPT
from .router import describe_tools, select_tool
from .tools import TOOLS


@dataclass
class Message:
    role: str
    content: str


def _format_response(message: str, model: str, tool_name: str, tool_output: str) -> str:
    """Create the final response string sent back to the caller."""

    reasoning = f"Using the `{tool_name}` tool" if tool_name != "idle" else "No specialised tool was used"
    context = f"\nTool output: {tool_output}" if tool_output else ""
    return (
        f"{SYSTEM_PROMPT.strip()}\n\n"
        f"Model: {model}\n"
        f"User asked: {message}\n"
        f"{reasoning}." + context + "\n"
        "Final answer: I hope this helps!"
    )


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

    final_answer = _format_response(message, model, tool_name, tool_output)
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
