"""Routing logic for choosing tools inside AgentKit."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Dict, Any
from .tools import TOOLS
from .llm_client import llm_client


async def select_tool(message: str, conversation_context: str = "") -> str:
    """Choose the most appropriate tool using enhanced LLM-based intelligent routing with context awareness."""
    
    # Analyze message complexity and context
    analysis = _analyze_message_context(message, conversation_context)
    
    # Create enhanced prompt for the LLM
    tool_descriptions = "\n".join(
        [f"- {name}: {tool.description}" for name, tool in TOOLS.items()]
    )

    # Enhanced routing prompt with context analysis
    routing_prompt = f"""You are AgentKit's intelligent routing system. Your job is to analyze user queries and conversation context to select the optimal tool for the best user experience.

AVAILABLE TOOLS:
{tool_descriptions}

CURRENT USER QUERY: "{message}"

CONVERSATION CONTEXT ANALYSIS:
- Message complexity: {analysis['complexity']}
- Contains factual questions: {analysis['needs_facts']}
- References AgentKit system: {analysis['about_agentkit']}  
- Memory-related intent: {analysis['memory_intent']}
- Conversational tone: {analysis['conversational']}

CONVERSATION CONTEXT:
{conversation_context if conversation_context else "No prior conversation"}

ENHANCED ROUTING RULES:
1. **Web Tool** - Use for:
   - Factual questions requiring current/real-time information
   - "Who/what/when/where/why/how" questions about external topics
   - Current events, news, market data, scientific facts
   - Company information, person profiles, technical specifications
   - Research queries needing up-to-date information
   - When conversation context suggests need for external knowledge

2. **RAG Tool** - Use for:
   - Questions about AgentKit architecture, features, or setup
   - Documentation requests about this system
   - "How does AgentKit work" type questions
   - Technical implementation details of AgentKit

3. **Memory Tool** - Use for:
   - Explicit requests to remember/store information
   - Requests to recall previously mentioned information
   - "Remember when I said...", "What did I tell you about..."
   - Managing personal preferences or stored data

4. **Idle Tool** - Use for:
   - Simple greetings, thanks, acknowledgments
   - General conversational responses without tool needs
   - Casual conversation that doesn't require external information
   - When no other tool is clearly needed

CONTEXT-AWARE DECISION MAKING:
- Consider conversation flow and previous tool usage
- Prioritize user intent over literal keywords
- If uncertain between tools, favor the one that provides more value
- Consider if the user might benefit from chained tool usage

Respond with ONLY the tool name: web, rag, memory, or idle"""

    try:
        # Use LLM to intelligently select the tool
        llm_response = await llm_client.generate_response(routing_prompt, "gemini")
        selected_tool = llm_response.strip().lower()
        
        # Validate and log the selection
        if selected_tool in TOOLS:
            _log_routing_decision(message, selected_tool, analysis, "llm")
            return selected_tool
        else:
            # Enhanced fallback with context
            fallback_tool = _enhanced_fallback_routing(message, conversation_context, analysis)
            _log_routing_decision(message, fallback_tool, analysis, "fallback")
            return fallback_tool

    except Exception as e:
        print(f"Error in LLM routing: {e}")
        fallback_tool = _enhanced_fallback_routing(message, conversation_context, analysis)
        _log_routing_decision(message, fallback_tool, analysis, "error_fallback")
        return fallback_tool


def _analyze_message_context(message: str, conversation_context: str = "") -> Dict[str, Any]:
    """Analyze message and context for better routing decisions."""
    lowered = message.lower()
    
    # Analyze message complexity
    complexity = "complex" if len(message.split()) > 10 or "?" in message else "simple"
    
    # Check for factual question patterns
    factual_patterns = [
        r'\b(who|what|when|where|why|how)\s+',
        r'\b(tell me about|explain|describe)\s+',
        r'\b(latest|current|recent|today)\s+',
        r'\b(price|cost|value)\s+',
    ]
    needs_facts = any(re.search(pattern, lowered) for pattern in factual_patterns)
    
    # Check for AgentKit-specific queries
    agentkit_keywords = ["agentkit", "architecture", "setup", "documentation", "how does this work"]
    about_agentkit = any(keyword in lowered for keyword in agentkit_keywords)
    
    # Check for memory intent
    memory_keywords = ["remember", "recall", "store", "save", "said", "told", "mentioned"]
    memory_intent = any(keyword in lowered for keyword in memory_keywords)
    
    # Check conversational tone
    conversational_patterns = ["hello", "hi", "thanks", "thank you", "goodbye", "bye"]
    conversational = any(pattern in lowered for pattern in conversational_patterns)
    
    return {
        "complexity": complexity,
        "needs_facts": needs_facts,
        "about_agentkit": about_agentkit,
        "memory_intent": memory_intent,
        "conversational": conversational,
        "has_context": bool(conversation_context.strip()),
        "word_count": len(message.split())
    }


def _enhanced_fallback_routing(message: str, conversation_context: str, analysis: Dict[str, Any]) -> str:
    """Enhanced fallback routing with context awareness."""
    lowered = message.lower()
    
    # Use analysis results for smarter fallback
    if analysis['about_agentkit']:
        return "rag"
    elif analysis['memory_intent']:
        return "memory"
    elif analysis['needs_facts'] or analysis['complexity'] == "complex":
        return "web"
    elif analysis['conversational']:
        return "idle"
    
    # Traditional keyword matching as final fallback
    if any(word in lowered for word in ["search", "find", "who", "what", "when", "where", "news", "latest"]):
        return "web"
    elif any(word in lowered for word in ["architecture", "setup", "explain agentkit", "how does agentkit"]):
        return "rag"
    elif any(word in lowered for word in ["remember", "recall", "store", "memory", "said"]):
        return "memory"
    else:
        return "idle"


# Storage for routing metrics and logs
_routing_metrics = {
    "total_routes": 0,
    "tool_usage": {"web": 0, "rag": 0, "memory": 0, "idle": 0},
    "routing_methods": {"llm": 0, "fallback": 0, "error_fallback": 0},
    "last_reset": datetime.now().isoformat()
}


def _log_routing_decision(message: str, selected_tool: str, analysis: Dict[str, Any], method: str):
    """Log routing decisions for monitoring and improvement."""
    _routing_metrics["total_routes"] += 1
    _routing_metrics["tool_usage"][selected_tool] += 1
    _routing_metrics["routing_methods"][method] += 1
    
    # In production, this could write to a proper logging system
    print(f"[ROUTING] Tool: {selected_tool}, Method: {method}, Analysis: {analysis['complexity']}")


def get_routing_metrics() -> Dict[str, Any]:
    """Get current routing metrics for monitoring."""
    return _routing_metrics.copy()


def reset_routing_metrics():
    """Reset routing metrics (useful for testing)."""
    global _routing_metrics
    _routing_metrics = {
        "total_routes": 0,
        "tool_usage": {"web": 0, "rag": 0, "memory": 0, "idle": 0},
        "routing_methods": {"llm": 0, "fallback": 0, "error_fallback": 0},
        "last_reset": datetime.now().isoformat()
    }
def _fallback_keyword_routing(message: str) -> str:
    """Legacy fallback keyword-based routing when LLM routing fails."""
    return _enhanced_fallback_routing(message, "", _analyze_message_context(message, ""))


def describe_tools() -> str:
    """Return a human readable list of available tools."""

    lines = [f"- {tool.name}: {tool.description}" for tool in TOOLS.values()]
    return "\n".join(lines)
