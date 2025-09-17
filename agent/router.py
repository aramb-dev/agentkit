"""Routing logic for choosing tools inside AgentKit."""

from __future__ import annotations

from typing import Optional

from .tools import TOOLS

_TOOL_KEYWORDS = {
    "web": ("search", "news", "lookup", "find", "google", "web", "internet", "online"),
    "rag": (
        "document",
        "docs",
        "explain",
        "architecture",
        "what is",
        "how does",
        "tell me about",
    ),
    "memory": ("remember", "recall", "remind", "save", "store", "memory", "note"),
}


def select_tool(message: str) -> str:
    """Choose the most appropriate tool based on simple keyword heuristics."""

    lowered = message.lower()

    # Score each tool based on keyword matches
    tool_scores = {}
    for tool_name, keywords in _TOOL_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > 0:
            tool_scores[tool_name] = score

    # Return the tool with the highest score, or idle if no matches
    if tool_scores:
        best_tool = max(tool_scores.items(), key=lambda x: x[1])
        return best_tool[0]

    return "idle"


def describe_tools() -> str:
    """Return a human readable list of available tools."""

    lines = [f"- {tool.name}: {tool.description}" for tool in TOOLS.values()]
    return "\n".join(lines)
