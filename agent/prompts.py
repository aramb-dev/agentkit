"""Static prompt templates used by the AgentKit PoC."""

from textwrap import dedent

SYSTEM_PROMPT = dedent(
    """
    You are AgentKit, a modular proof-of-concept agent. When possible you should
    lean on the available tools, explain your reasoning briefly, and keep the
    final answer actionable for the user.
    """
)

SUMMARY_PROMPT = "Conversation summary: {conversation}"

AVAILABLE_TOOLS_PROMPT = dedent(
    """
    Available tools:
    {tool_overview}
    """
)
