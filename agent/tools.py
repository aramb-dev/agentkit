from langchain.tools import tool
from langchain_tavily import TavilySearch
from typing import Dict

web_search_tool = TavilySearch()


@tool
def retriever_tool(query: str) -> str:
    """
    A tool that simulates retrieving a document chunk.
    """
    return f"Fake retrieved doc chunk for '{query}': This is a document about the meaning of life."


# In-memory store for the memory tool
memory_store: Dict[str, str] = {}


@tool
def memory_tool(action: str, data: str = "") -> str:
    """
    A tool that simulates a memory store.
    Actions: 'read', 'write'
    """
    if action == "write":
        # For simplicity, we'll just store the last piece of data.
        # A real implementation would handle this differently.
        memory_store["last_entry"] = data
        return f"Data written to memory."
    elif action == "read":
        return memory_store.get("last_entry", "No data in memory.")
    else:
        return "Invalid action. Use 'read' or 'write'."
