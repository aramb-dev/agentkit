"""Simple tool implementations for the AgentKit PoC."""

from __future__ import annotations

import asyncio
import datetime as _dt
import random
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, Iterable


ToolFn = Callable[[str], "ToolResult"]
ToolResult = str | Awaitable[str]


@dataclass(slots=True)
class Tool:
    """Descriptor for an agent tool."""

    name: str
    description: str
    fn: ToolFn

    async def run(self, query: str) -> str:
        """Execute the wrapped function regardless of sync/async signature."""

        if asyncio.iscoroutinefunction(self.fn):
            return await self.fn(query)  # type: ignore[arg-type]

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.fn, query)


# Basic fake data to keep the demo self-contained.
_FAKE_NEWS = [
    "Modular agents gain popularity in enterprise automation",
    "Researchers release lightweight open-source LLMs",
    "Startups embrace synthetic data pipelines"
]

_FAKE_DOCUMENTS = {
    "architecture": "AgentKit is organised around a router, tools, and a summariser.",
    "memory": "The memory tool simply echoes context back to the caller.",
}


def _web_search(query: str) -> str:
    headline = random.choice(_FAKE_NEWS)
    return f"Top headline for '{query}': {headline}."


def _retrieve_context(query: str) -> str:
    matches: Iterable[str] = (
        doc for key, doc in _FAKE_DOCUMENTS.items() if key in query.lower()
    )
    return "\n".join(matches) or "No matching documents found, relying on general knowledge."


def _memory_lookup(query: str) -> str:
    now = _dt.datetime.utcnow().isoformat(timespec="seconds")
    return f"[{now} UTC] Memory reflection: you asked me to remember '{query}'."


def _idle(_: str) -> str:
    return "No tool looked relevant, responding from prior knowledge."


TOOLS: Dict[str, Tool] = {
    "web": Tool(
        name="web",
        description="Return a mocked web search headline for the query.",
        fn=_web_search,
    ),
    "rag": Tool(
        name="rag",
        description="Retrieve short snippets from a fake document store.",
        fn=_retrieve_context,
    ),
    "memory": Tool(
        name="memory",
        description="Echo the query with a timestamp to simulate recall.",
        fn=_memory_lookup,
    ),
    "idle": Tool(
        name="idle",
        description="Fallback response when no specialised tool matches.",
        fn=_idle,
    ),
}
