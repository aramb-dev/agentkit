from typing import Literal, Optional


def route_query(
    query: str,
) -> Optional[Literal["web_search_tool", "retriever_tool", "memory_tool"]]:
    """
    Inspects the user query and decides which tool to use.
    """
    query_lower = query.lower()
    if "search" in query_lower or "find" in query_lower:
        return "web_search_tool"
    if "retrieve" in query_lower or "document" in query_lower:
        return "retriever_tool"
    if (
        "remember" in query_lower
        or "recall" in query_lower
        or "write" in query_lower
        or "read" in query_lower
    ):
        return "memory_tool"
    return None
