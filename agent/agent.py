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


async def run_agent(message: str, model: str) -> Dict[str, str]:
    """Entry point used by the FastAPI app."""

    history = [Message(role="user", content=message)]
    tool_name = await select_tool(message)  # Now async
    tool = TOOLS[tool_name]
    tool_output = await tool.run(message)

    if tool_name != "idle" and tool_output:
        history.append(Message(role="tool", content=f"{tool_name}: {tool_output}"))

    final_answer = await _format_response(message, model, tool_name, tool_output)
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
