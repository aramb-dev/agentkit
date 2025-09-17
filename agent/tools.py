"""Simple tool implementations for the AgentKit PoC."""

from __future__ import annotations

import asyncio
import datetime as _dt
import os
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, List

from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables
load_dotenv()


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


# Initialize Tavily client
tavily_client = None
tavily_api_key = os.getenv("TAVILY_API_KEY")
if tavily_api_key:
    try:
        tavily_client = TavilyClient(api_key=tavily_api_key)
    except Exception as e:
        print(f"Warning: Failed to initialize Tavily client: {e}")


async def _web_search(query: str) -> str:
    """Search the web using Tavily API for real, current information."""
    if tavily_client:
        try:
            # Run Tavily search in thread pool to avoid async SSL issues
            def run_search():
                return tavily_client.search(  # type: ignore
                    query=query, search_depth="basic", max_results=3
                )

            loop = asyncio.get_running_loop()
            search_result = await loop.run_in_executor(None, run_search)

            if search_result and "results" in search_result:
                results = search_result["results"]
                if results:
                    formatted_results = []
                    for i, result in enumerate(results[:3], 1):
                        title = result.get("title", "No title")
                        content = result.get("content", "No content available")
                        url = result.get("url", "")

                        # Truncate content to keep results manageable
                        content = (
                            content[:200] + "..." if len(content) > 200 else content
                        )

                        formatted_results.append(
                            f"{i}. **{title}**\n   {content}\n   Source: {url}"
                        )

                    timestamp = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                    return (
                        f"Web search results for '{query}' (as of {timestamp}):\n\n"
                        + "\n\n".join(formatted_results)
                    )

            return f"No search results found for '{query}'. Tavily search returned empty results."

        except Exception as e:
            print(f"Error with Tavily search: {e}")
            return _fallback_web_search(query)

    # Fallback when Tavily is not available
    return _fallback_web_search(query)


def _fallback_web_search(query: str) -> str:
    """Fallback web search with simulated results when Tavily is not available."""
    import random

    news_items = [
        "Modular AI agents gain popularity in enterprise automation, showing 40% efficiency improvements",
        "Researchers release lightweight open-source LLMs that run on consumer hardware",
        "Startups embrace synthetic data pipelines to overcome training data limitations",
        "New study shows AI agents reduce manual task completion time by 60%",
        "Tech giants invest heavily in autonomous agent development for business applications",
    ]

    headline = random.choice(news_items)
    timestamp = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"Search results for '{query}' (as of {timestamp}):\n\n• {headline}\n\n[Note: This is simulated search data - Tavily API not available]"


def _retrieve_context(query: str) -> str:
    """Retrieve documentation with more detailed context."""
    docs = {
        "architecture": """AgentKit Architecture Overview:
- Router: Analyzes user queries and selects appropriate tools based on keyword matching
- Tools: Modular components that handle specific tasks (web search, document retrieval, memory)
- LLM Integration: Uses Google Gemini to generate natural, contextual responses
- Response Formatter: Combines tool outputs with AI-generated explanations""",
        "memory": """Memory System:
- Stores user queries with timestamps for recall functionality
- Provides context for ongoing conversations
- Simulates persistent memory across interactions
- Can be extended to use vector databases for semantic search""",
        "setup": """AgentKit Setup:
- Built with FastAPI for API endpoints
- Streamlit UI for web interface
- LangChain integration for LLM connectivity
- Environment variables for API key management""",
    }

    query_lower = query.lower()
    matched_docs = []

    for key, content in docs.items():
        if key in query_lower or any(word in query_lower for word in key.split()):
            matched_docs.append(f"=== {key.title()} ===\n{content}")

    if matched_docs:
        return "\n\n".join(matched_docs)

    return f"No specific documentation found for '{query}'. Available topics: architecture, memory, setup"


def _memory_lookup(query: str) -> str:
    """Enhanced memory function with better context."""
    now = _dt.datetime.utcnow().isoformat(timespec="seconds")

    # Extract what the user wants to remember/recall
    if "remember" in query.lower():
        content = query.lower().replace("remember", "").replace("that", "").strip()
        return f"[{now} UTC] Stored in memory: {content}\n\nI'll remember this information for our conversation."
    elif "recall" in query.lower() or "what did" in query.lower():
        return f"[{now} UTC] Memory recall request for: {query}\n\n[Note: This is a demonstration - in a full implementation, I would search stored memories]"
    else:
        return f"[{now} UTC] Memory operation: {query}\n\nMemory system is ready to store or recall information."


def _idle(query: str) -> str:
    """Provide helpful fallback response when no specialized tool is relevant."""
    return f"I understand you said: '{query}'. While I don't have a specialized tool for this, I'm here to help with web searches, document explanations, or memory functions."


TOOLS: Dict[str, Tool] = {
    "web": Tool(
        name="web",
        description="Search the web for current information and news on any topic using Tavily API",
        fn=_web_search,
    ),
    "rag": Tool(
        name="rag",
        description="Retrieve documentation and explanations about AgentKit architecture and features",
        fn=_retrieve_context,
    ),
    "memory": Tool(
        name="memory",
        description="Store information in memory or recall previously stored information",
        fn=_memory_lookup,
    ),
    "idle": Tool(
        name="idle",
        description="General conversation and assistance when no specific tool is needed",
        fn=_idle,
    ),
}
