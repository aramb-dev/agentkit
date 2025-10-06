"""Agent orchestration entrypoints."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List

from .prompts import AVAILABLE_TOOLS_PROMPT, SUMMARY_PROMPT, SYSTEM_PROMPT
from .router import describe_tools, select_tool
from .tools import TOOLS
from .llm_client import llm_client
from .tool_chain import tool_chain


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
    search_mode: str = "auto",
) -> Dict[str, str]:
    """Entry point used by the FastAPI app with conversation history and search mode support."""
    import time
    start_time = time.time()

    # Convert conversation history to Message objects
    history = []
    for msg in conversation_history[-10:]:  # Keep last 10 messages for context
        if msg.get("role") in ["user", "assistant"]:
            history.append(Message(role=msg["role"], content=msg["content"]))

    # Add current user message
    history.append(Message(role="user", content=message))

    # Create context from recent conversation for enhanced routing
    recent_context = "\n".join([f"{msg.role}: {msg.content}" for msg in history[-3:]])

    # Check if this query could benefit from tool chaining
    chain_steps = await tool_chain.detect_chain_opportunity(message, recent_context)
    
    if chain_steps:
        # Execute tool chain
        chain_result = await tool_chain.execute_chain(chain_steps, namespace)
        
        if chain_result.success:
            # Combine results from chained tools
            combined_output = "\n\n".join([
                f"**{tool}**: {result}" for tool, result in chain_result.results.items()
            ])
            
            # Add chain execution info to history
            history.append(Message(
                role="tool", 
                content=f"chain: {' → '.join(chain_result.execution_order)} | {combined_output}"
            ))
            
            # Format response with chain context
            conversation_context = "\n".join([f"{msg.role}: {msg.content}" for msg in history[-5:]])
            final_answer = await _format_chain_response(
                message, model, chain_result.results, chain_result.execution_order, conversation_context
            )
            
            execution_time = time.time() - start_time
            summary = _summarise(history, final_answer)
            
            return {
                "answer": final_answer,
                "tool_used": f"chain({' → '.join(chain_result.execution_order)})",
                "tool_output": combined_output,
                "model": model,
                "context": AVAILABLE_TOOLS_PROMPT.format(tool_overview=describe_tools()),
                "summary": summary,
                "chain_execution": True,
                "execution_time": execution_time,
                "chain_details": {
                    "steps": len(chain_steps),
                    "tools": chain_result.execution_order,
                    "success": chain_result.success
                }
            }
        else:
            # Chain failed, fall back to single tool
            print(f"Tool chain failed: {chain_result.error}, falling back to single tool")

    # Standard single tool execution with search mode override
    if search_mode == "web":
        tool_name = "web"
    elif search_mode == "documents":
        tool_name = "rag"
    elif search_mode == "hybrid":
        tool_name = "hybrid"
    else:
        # Auto mode - let the router decide
        tool_name = await select_tool(f"Current message: {message}", f"Recent conversation:\n{recent_context}")
    
    tool = TOOLS[tool_name]

    # Execute single tool with error handling
    tool_output = ""
    tool_error = None
    
    try:
        # Handle RAG tool with namespace parameter
        if tool_name == "rag":
            from .tools import _retrieve_context
            tool_output = await _retrieve_context(message, namespace=namespace)
        # Handle hybrid tool with namespace parameter
        elif tool_name == "hybrid":
            from .tools import _hybrid_search
            tool_output = await _hybrid_search(message, namespace=namespace)
        else:
            tool_output = await tool.run(message)
    except Exception as e:
        tool_error = str(e)
        tool_output = f"Tool execution failed: {tool_error}"
        print(f"Tool {tool_name} execution error: {e}")

    if tool_name != "idle" and tool_output:
        history.append(Message(role="tool", content=f"{tool_name}: {tool_output}"))

    # Include conversation context in response generation
    conversation_context = "\n".join([f"{msg.role}: {msg.content}" for msg in history[-5:]])
    
    final_answer = await _format_response_with_context(
        message, model, tool_name, tool_output, conversation_context
    )
    
    execution_time = time.time() - start_time
    summary = _summarise(history, final_answer)
    tool_overview = AVAILABLE_TOOLS_PROMPT.format(tool_overview=describe_tools())

    return {
        "answer": final_answer,
        "tool_used": tool_name,
        "tool_output": tool_output,
        "model": model,
        "context": tool_overview,
        "summary": summary,
        "chain_execution": False,
        "execution_time": execution_time,
        "tool_error": tool_error
    }


async def _format_chain_response(
    message: str,
    model: str, 
    chain_results: Dict[str, str],
    execution_order: List[str],
    conversation_context: str
) -> str:
    """Format response when multiple tools were used in a chain."""
    
    # Create a summary of what each tool contributed
    tool_contributions = []
    for tool_name in execution_order:
        result = chain_results.get(tool_name, "No result")
        tool_contributions.append(f"- **{tool_name.title()}**: {result[:200]}{'...' if len(result) > 200 else ''}")
    
    contributions_summary = "\n".join(tool_contributions)
    
    prompt = f"""You are AgentKit, a powerful AI agent that just executed a sophisticated workflow. 

User asked: "{message}"

Recent conversation context:
{conversation_context}

I used multiple tools in sequence to provide a comprehensive answer:
{contributions_summary}

Your task is to synthesize these results into a coherent, valuable response:

Guidelines:
- Acknowledge the comprehensive analysis you performed
- Synthesize information from all tools into a unified answer  
- Highlight connections and insights across the different tool results
- Be confident about the thoroughness of your analysis
- Show how the multi-step approach provided better results
- Present the information clearly and professionally
- Reference specific findings from each tool when relevant

Provide a confident, well-structured response that showcases the value of the multi-tool analysis."""

    return await llm_client.generate_response(prompt, model)


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
