"""Routing logic for choosing tools inside AgentKit."""

from __future__ import annotations

from typing import Optional

from .tools import TOOLS

_TOOL_KEYWORDS = {
    "web": ("search", "news", "lookup"),
    "rag": ("document", "docs", "explain", "architecture"),
    "memory": ("remember", "recall", "remind"),
}


def select_tool(message: str) -> str:
    """Choose the most appropriate tool based on simple keyword heuristics."""

    lowered = message.lower()
    for tool_name, keywords in _TOOL_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return tool_name
    return "idle"


def describe_tools() -> str:
    """Return a human readable list of available tools."""

    lines = [f"- {tool.name}: {tool.description}" for tool in TOOLS.values()]
    return "\n".join(lines)
