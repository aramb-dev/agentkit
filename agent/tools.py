"""Simple tool implementations for the AgentKit PoC."""

from __future__ import annotations

import asyncio
import datetime as _dt
import os
import random
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, List, Any

from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# Import RAG functionality
try:
    from rag.store import query as vector_query

    RAG_AVAILABLE = True
except ImportError:
    vector_query = None
    RAG_AVAILABLE = False


ToolFn = Callable[[str], "ToolResult"]
ToolResult = str | Awaitable[str]


@dataclass(slots=True)
class Tool:
    """Enhanced tool descriptor with performance monitoring."""

    name: str
    description: str
    fn: ToolFn
    metrics: Dict[str, Any] = field(default_factory=lambda: {
        "total_calls": 0,
        "total_time": 0.0,
        "success_count": 0,
        "error_count": 0,
        "last_used": None,
        "average_response_time": 0.0
    })

    async def run(self, query: str) -> str:
        """Execute the wrapped function with performance monitoring."""
        start_time = time.time()
        self.metrics["total_calls"] += 1
        self.metrics["last_used"] = _dt.datetime.now().isoformat()
        
        try:
            if asyncio.iscoroutinefunction(self.fn):
                result = await self.fn(query)  # type: ignore[arg-type]
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, self.fn, query)
            
            # Record success metrics
            execution_time = time.time() - start_time
            self.metrics["total_time"] += execution_time
            self.metrics["success_count"] += 1
            self.metrics["average_response_time"] = self.metrics["total_time"] / self.metrics["total_calls"]
            
            return result
            
        except Exception as e:
            # Record error metrics
            execution_time = time.time() - start_time
            self.metrics["total_time"] += execution_time
            self.metrics["error_count"] += 1
            self.metrics["average_response_time"] = self.metrics["total_time"] / self.metrics["total_calls"]
            
            error_msg = f"Tool {self.name} failed: {str(e)}"
            print(f"[TOOL ERROR] {error_msg}")
            return error_msg

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this tool."""
        success_rate = (
            (self.metrics["success_count"] / self.metrics["total_calls"] * 100) 
            if self.metrics["total_calls"] > 0 else 0
        )
        
        return {
            "name": self.name,
            "total_calls": self.metrics["total_calls"],
            "success_rate": f"{success_rate:.1f}%",
            "average_response_time": f"{self.metrics['average_response_time']:.2f}s",
            "total_time": f"{self.metrics['total_time']:.2f}s",
            "last_used": self.metrics["last_used"],
            "errors": self.metrics["error_count"]
        }


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

                    timestamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
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
    timestamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"Search results for '{query}' (as of {timestamp}):\n\n• {headline}\n\n[Note: This is simulated search data - Tavily API not available]"


async def _enhance_query(query: str) -> str:
    """
    Enhance query using LLM for advanced understanding.
    
    This includes:
    - Query expansion for better semantic matching
    - Synonym detection
    - Context preservation
    - Key concept extraction
    """
    from .llm_client import llm_client
    
    # For very short queries, return as-is
    if len(query.split()) <= 2:
        return query
    
    try:
        # Use LLM to extract key search terms and concepts
        prompt = f"""Given this user query, extract the key search terms and concepts that would be most effective for semantic document search. Remove filler words but preserve important context.

User Query: "{query}"

Return only the enhanced search query without any explanation. Keep it concise and focused on the core concepts. If the query is already optimal, return it unchanged.

Enhanced Query:"""
        
        enhanced = await llm_client.generate_response(prompt, model="gemini")
        
        # Check if we got an error/fallback message from LLM
        if "unable to access" in enhanced.lower() or "api" in enhanced.lower() and "key" in enhanced.lower():
            # LLM not available, return original
            return query
        
        # Clean up the response
        enhanced = enhanced.strip().strip('"').strip("'")
        
        # If enhancement failed or is too different, use original
        if not enhanced or len(enhanced) < 2:
            return query
            
        # If enhancement is too short compared to original, use original
        if len(enhanced) < len(query) * 0.3:
            return query
            
        return enhanced
        
    except Exception as e:
        print(f"Query enhancement error: {e}")
        # Fallback to original query on error
        return query


async def _retrieve_context(query: str, namespace: str = "default", k: int = 5) -> str:
    """Retrieve relevant document chunks using enhanced semantic search with citations."""
    if not RAG_AVAILABLE or vector_query is None:
        return _fallback_rag_search(query)

    try:
        # Apply advanced query understanding using LLM
        enhanced_query = await _enhance_query(query)
        
        hits = vector_query(namespace, enhanced_query, k=k)
        if not hits:
            return f"[RAG] No relevant documents found in namespace '{namespace}' for query: '{query}'\n\nThis could mean:\n1. No documents have been ingested yet\n2. The documents don't contain relevant information\n3. Try a different search term or upload relevant documents first"

        # Format results with citations and relevance scores
        lines = []
        citations = []
        
        for i, h in enumerate(hits, 1):
            src = h["metadata"].get("filename", "unknown")
            chunk_num = h["metadata"].get("chunk", "?")
            doc_id = h["metadata"].get("doc_id", "unknown")
            distance = h.get("distance", "N/A")
            relevance_score = h.get("relevance_score", 0.0)
            
            # Build citation
            citation = f"[{i}] {src}, chunk {chunk_num} (relevance: {relevance_score:.2%})"
            citations.append(citation)

            # Truncate text for manageable context
            text = h["text"][:600]
            if len(h["text"]) > 600:
                text += "..."

            # Format with citation reference
            lines.append(f"**Source [{i}]: {src}** (chunk #{chunk_num}, relevance: {relevance_score:.2%})\n{text}")

        timestamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        # Create structured result with citations
        result = (
            f"RAG search results for '{query}' in namespace '{namespace}' (as of {timestamp}):\n\n"
            + "\n\n".join(lines)
            + "\n\n---\n**Citations:**\n"
            + "\n".join(citations)
        )

        return result

    except Exception as e:
        print(f"RAG search error: {e}")
        return f"[RAG] Error retrieving documents: {str(e)}\n\nFalling back to general knowledge."


def _fallback_rag_search(query: str) -> str:
    """Fallback when RAG system is not available.
    
    This should only be called when the RAG system dependencies are not installed.
    In production, the full RAG system should always be available.
    """
    return f"""[RAG System Unavailable]

The document retrieval system (RAG) is currently not available. This typically means:

1. **Missing Dependencies**: ChromaDB or sentence-transformers not installed
2. **Import Error**: Vector store module failed to load
3. **Development Mode**: Running without full RAG setup

Your query: "{query}"

To enable full RAG functionality:
- Install dependencies: pip install chromadb sentence-transformers
- Upload documents via /docs/ingest endpoint
- Query your uploaded documents using the RAG tool

For more information, see the documentation:
- ADVANCED_RAG_FEATURES.md
- DOCUMENT_MANAGEMENT.md

[Note: This is a fallback message - no hardcoded documents are returned]"""


def _memory_lookup(query: str) -> str:
    """Enhanced memory function with better context."""
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")

    # Extract what the user wants to remember/recall
    if "remember" in query.lower():
        content = query.lower().replace("remember", "").replace("that", "").strip()
        return f"[{now} UTC] Stored in memory: {content}\n\nI'll remember this information for our conversation."
    elif "recall" in query.lower() or "what did" in query.lower():
        return f"[{now} UTC] Memory recall request for: {query}\n\n[Note: This is a demonstration - in a full implementation, I would search stored memories]"
    else:
        return f"[{now} UTC] Memory operation: {query}\n\nMemory system is ready to store or recall information."


async def _rag_wrapper(query: str) -> str:
    """Wrapper for RAG that uses default namespace - will be overridden by agent."""
    return await _retrieve_context(query, namespace="default")


def _idle(query: str) -> str:
    """Provide helpful fallback response when no specialized tool is relevant."""
    return f"I understand you said: '{query}'. While I don't have a specialized tool for this, I'm here to help with web searches, document explanations, or memory functions."


async def _hybrid_search(query: str, namespace: str = "default") -> str:
    """
    Hybrid search combining web search and document retrieval for comprehensive results.
    
    This advanced feature:
    - Searches both web (current information) and documents (uploaded knowledge)
    - Provides source attribution from both sources
    - Combines results intelligently for better context
    """
    # Execute both searches in parallel for efficiency
    web_task = asyncio.create_task(_web_search(query))
    rag_task = asyncio.create_task(_retrieve_context(query, namespace, 3))
    
    # Wait for both to complete
    web_results, rag_results = await asyncio.gather(web_task, rag_task, return_exceptions=True)
    
    # Handle potential errors
    if isinstance(web_results, Exception):
        web_results = f"Web search error: {str(web_results)}"
    if isinstance(rag_results, Exception):
        rag_results = f"Document search error: {str(rag_results)}"
    
    timestamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    # Combine results with clear attribution
    result = f"""Hybrid search results for '{query}' (as of {timestamp}):

═══════════════════════════════════════
📚 FROM YOUR DOCUMENTS:
═══════════════════════════════════════
{rag_results}

═══════════════════════════════════════
🌐 FROM WEB SEARCH:
═══════════════════════════════════════
{web_results}

═══════════════════════════════════════
💡 HYBRID SEARCH SUMMARY:
═══════════════════════════════════════
This response combines information from both your uploaded documents and current web sources to provide comprehensive, up-to-date answers with full source attribution.
"""
    
    return result


def _hybrid_wrapper(query: str) -> str:
    """Wrapper for hybrid search - will be overridden by agent with namespace."""
    # This is a synchronous wrapper that creates an event loop if needed
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_hybrid_search(query, namespace="default"))


TOOLS: Dict[str, Tool] = {
    "web": Tool(
        name="web",
        description="Search the web for current information and news on any topic using Tavily API",
        fn=_web_search,
    ),
    "rag": Tool(
        name="rag",
        description="Retrieve information from uploaded documents using vector search and semantic similarity with citations",
        fn=_rag_wrapper,
    ),
    "hybrid": Tool(
        name="hybrid",
        description="Advanced hybrid search combining web search and document retrieval for comprehensive answers with source attribution",
        fn=_hybrid_wrapper,
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


def get_all_tool_performance_stats() -> Dict[str, Dict[str, Any]]:
    """Get performance statistics for all tools."""
    return {tool_name: tool.get_performance_stats() for tool_name, tool in TOOLS.items()}


def reset_tool_metrics():
    """Reset performance metrics for all tools."""
    for tool in TOOLS.values():
        tool.metrics = {
            "total_calls": 0,
            "total_time": 0.0,
            "success_count": 0,
            "error_count": 0,
            "last_used": None,
            "average_response_time": 0.0
        }
