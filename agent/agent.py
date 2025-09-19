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
        # For idle responses, be more assertive about capabilities
        prompt = f"""You are AgentKit, a proactive and helpful AI agent. The user said: "{message}"

You are designed to be decisive and take action. You have these powerful capabilities:
- Web search: You can find current information on any topic
- Document explanations: You can explain complex topics and architectures
- Memory functions: You can remember and recall information

Important guidelines:
- Be confident and assertive in your responses
- If you don't know something that could be searched, mention that you would search for it
- Don't ask permission to use tools - just state what you can do
- Be direct and actionable in your communication
- Show enthusiasm for helping solve problems

Respond naturally and confidently."""

        return await llm_client.generate_response(prompt, model)
    else:
        # For tool-specific responses, be confident about the results
        prompt = f"""You are AgentKit, a confident and helpful AI agent. The user asked: "{message}"

I used my {tool_name} capability and found this information: {tool_output}

Guidelines for your response:
- Be assertive and confident about the information you found
- Present the results clearly and professionally
- Don't hedge or apologize unnecessarily
- If the information seems incomplete, mention you can search for more details
- Be direct and helpful
- Show that you're actively working to provide the best possible answer

Provide a confident, well-formatted response based on the information gathered."""

        return await llm_client.generate_response(prompt, model)


def _summarise(history: List[Message], final_answer: str) -> str:
    conversation = "\n".join(f"{msg.role}: {msg.content}" for msg in history)
    conversation += f"\nagent: {final_answer}"
    return SUMMARY_PROMPT.format(conversation=conversation)


async def run_agent_with_history(
    message: str,
    model: str,
    conversation_history: List[Dict],
    namespace: str = "default",
    session_id: str = "default",
) -> Dict[str, str]:
    """Entry point used by the FastAPI app with conversation history support."""

    # Convert conversation history to Message objects
    history = []
    for msg in conversation_history[-10:]:  # Keep last 10 messages for context
        if msg.get("role") in ["user", "assistant"]:
            history.append(Message(role=msg["role"], content=msg["content"]))

    # Add current user message
    history.append(Message(role="user", content=message))

    # Create context from recent conversation for tool selection
    recent_context = "\n".join([f"{msg.role}: {msg.content}" for msg in history[-3:]])

    tool_name = await select_tool(
        f"Recent conversation:\n{recent_context}\n\nCurrent message: {message}"
    )
    tool = TOOLS[tool_name]

    # Handle RAG tool with namespace parameter
    if tool_name == "rag":
        from .tools import _retrieve_context

        tool_output = _retrieve_context(message, namespace=namespace)
    else:
        tool_output = await tool.run(message)

    if tool_name != "idle" and tool_output:
        history.append(Message(role="tool", content=f"{tool_name}: {tool_output}"))

    # Include conversation context in response generation
    conversation_context = "\n".join(
        [f"{msg.role}: {msg.content}" for msg in history[-5:]]
    )
    final_answer = await _format_response_with_context(
        message, model, tool_name, tool_output, conversation_context
    )
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


async def _format_response_with_context(
    message: str,
    model: str,
    tool_name: str,
    tool_output: str,
    conversation_context: str,
) -> str:
    """Create the final response string with conversation context."""

    if tool_name == "idle":
        prompt = f"""You are AgentKit, a proactive and helpful AI agent.

Recent conversation context:
{conversation_context}

Current user message: "{message}"

You are designed to be decisive and take action. You have these powerful capabilities:
- Web search: You can find current information on any topic
- Document explanations: You can explain complex topics and architectures
- Memory functions: You can remember and recall information

Important guidelines:
- Be confident and assertive in your responses
- Reference previous conversation when relevant
- If you don't know something that could be searched, mention that you would search for it
- Don't ask permission to use tools - just state what you can do
- Be direct and actionable in your communication
- Show enthusiasm for helping solve problems

Respond naturally and confidently, taking into account the conversation history."""

        return await llm_client.generate_response(prompt, model)
    else:
        prompt = f"""You are AgentKit, a confident and helpful AI agent.

Recent conversation context:
{conversation_context}

Current user message: "{message}"

I used my {tool_name} capability and found this information: {tool_output}

Guidelines for your response:
- Be assertive and confident about the information you found
- Reference previous conversation when relevant to provide better context
- Present the results clearly and professionally
- Don't hedge or apologize unnecessarily
- If the information seems incomplete, mention you can search for more details
- Be direct and helpful
- Show that you're actively working to provide the best possible answer

Provide a confident, well-formatted response based on the information gathered and conversation history."""

        return await llm_client.generate_response(prompt, model)


async def run_agent(message: str, model: str) -> Dict[str, str]:
    """Entry point used by the FastAPI app - backwards compatibility."""
    return await run_agent_with_history(message, model, [])
