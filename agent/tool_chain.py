"""Tool chaining capabilities for complex workflows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

from .tools import TOOLS, Tool
from .llm_client import llm_client


class ChainStrategy(Enum):
    """Strategies for tool chaining."""
    SEQUENTIAL = "sequential"  # Tools execute one after another
    PARALLEL = "parallel"     # Tools execute simultaneously 
    CONDITIONAL = "conditional"  # Next tool depends on previous result


@dataclass
class ChainStep:
    """A single step in a tool chain."""
    tool_name: str
    query: str
    depends_on: Optional[List[str]] = None  # Step names this depends on
    condition: Optional[str] = None  # Condition for conditional execution
    

@dataclass
class ChainResult:
    """Result from executing a tool chain."""
    success: bool
    results: Dict[str, str]  # tool_name -> result
    execution_order: List[str]
    total_time: float
    error: Optional[str] = None


class ToolChain:
    """Manages execution of tool chains for complex workflows."""
    
    def __init__(self):
        self.chains: Dict[str, List[ChainStep]] = {}
        self.execution_metrics: Dict[str, Any] = {}
    
    async def detect_chain_opportunity(self, message: str, conversation_context: str = "") -> Optional[List[ChainStep]]:
        """Detect if a query could benefit from tool chaining."""
        
        # Enhanced prompt for chain detection
        chain_detection_prompt = f"""You are AgentKit's workflow analyzer. Analyze this user query to determine if it EXPLICITLY needs multiple tools working together.

USER QUERY: "{message}"

CONVERSATION CONTEXT:
{conversation_context if conversation_context else "No prior context"}

AVAILABLE TOOLS:
- web: Search for current information and facts
- rag: Retrieve information from uploaded documents  
- memory: Store or recall personal information
- idle: General conversation

IMPORTANT: Only suggest chaining when the user EXPLICITLY requests multiple actions. Simple queries should use SINGLE tool.

CHAIN PATTERNS TO DETECT (be conservative):

1. **RESEARCH + MEMORY**: User explicitly asks to find AND remember/save information
   Example: "Find Tesla stock price and remember it" → Chain: web → memory
   NOT: "Find Tesla stock price" → SINGLE

2. **RECALL + SEARCH**: User explicitly references previous info AND asks for new search
   Example: "Based on what I told you about my project, find related tools" → Chain: memory → web
   NOT: "Find project tools" → SINGLE

3. **COMPARE DOCUMENTS + WEB**: User asks to compare internal docs with external info
   Example: "Compare our budget document with current market rates" → Chain: rag → web
   NOT: "What are current market rates" → SINGLE

4. **CONVERSATIONAL**: Simple greetings, thanks, questions without multiple actions
   Examples: "hello", "thanks", "what is X?" → SINGLE

Analyze the query and respond with ONE of:
- SINGLE: Query needs only one tool (most common)
- SEQUENTIAL: Query explicitly needs multiple tools in sequence
- PARALLEL: Query explicitly needs multiple tools simultaneously
- CONDITIONAL: Next tool explicitly depends on first tool's result

Be CONSERVATIVE - when in doubt, choose SINGLE. Only chain when user explicitly requests multiple actions."""

        try:
            response = await llm_client.generate_response(chain_detection_prompt, "gemini")
            return self._parse_chain_response(response, message)
        except Exception as e:
            print(f"Error in chain detection: {e}")
            return None
    
    def _parse_chain_response(self, response: str, original_message: str) -> Optional[List[ChainStep]]:
        """Parse LLM response to create chain steps."""
        response = response.strip().lower()
        
        if response.startswith("single"):
            return None
        
        # Check if this is a simple greeting or conversational message
        simple_patterns = ["hello", "hi", "thanks", "thank you", "goodbye", "bye"]
        if any(pattern in original_message.lower() for pattern in simple_patterns):
            return None
            
        # Simple pattern matching for common chains
        if "web" in response and "memory" in response:
            # Only create chain if there's clear intent for both search AND memory
            if any(word in original_message.lower() for word in ["remember", "save", "store"]):
                return [
                    ChainStep(tool_name="web", query=original_message),
                    ChainStep(tool_name="memory", query=f"Remember: {original_message}", depends_on=["web"])
                ]
        elif "memory" in response and "web" in response:
            # Only create chain if there's clear recall + search intent
            if any(word in original_message.lower() for word in ["recall", "based on", "from earlier"]):
                return [
                    ChainStep(tool_name="memory", query=f"Recall context for: {original_message}"),
                    ChainStep(tool_name="web", query=original_message, depends_on=["memory"])
                ]
        elif "rag" in response and "web" in response:
            # Only create chain for explicit comparisons or complex queries
            if any(word in original_message.lower() for word in ["compare", "versus", "both", "also"]):
                return [
                    ChainStep(tool_name="rag", query=original_message),
                    ChainStep(tool_name="web", query=original_message, depends_on=["rag"])
                ]
        
        return None
    
    async def execute_chain(self, steps: List[ChainStep], namespace: str = "default") -> ChainResult:
        """Execute a tool chain with proper dependency handling."""
        import time
        start_time = time.time()
        
        results: Dict[str, str] = {}
        execution_order: List[str] = []
        
        try:
            # Simple sequential execution for now
            for step in steps:
                # Check dependencies
                if step.depends_on:
                    missing_deps = [dep for dep in step.depends_on if dep not in results]
                    if missing_deps:
                        raise ValueError(f"Missing dependencies for {step.tool_name}: {missing_deps}")
                
                # Execute the tool
                tool = TOOLS[step.tool_name]
                
                # Handle RAG tool with namespace
                if step.tool_name == "rag":
                    from .tools import _retrieve_context
                    result = _retrieve_context(step.query, namespace=namespace)
                else:
                    result = await tool.run(step.query)
                
                results[step.tool_name] = result
                execution_order.append(step.tool_name)
            
            total_time = time.time() - start_time
            
            return ChainResult(
                success=True,
                results=results,
                execution_order=execution_order,
                total_time=total_time
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            return ChainResult(
                success=False,
                results=results,
                execution_order=execution_order,
                total_time=total_time,
                error=str(e)
            )
    
    async def execute_parallel_tools(self, tool_queries: Dict[str, str], namespace: str = "default") -> Dict[str, str]:
        """Execute multiple tools in parallel for efficiency."""
        async def run_tool(tool_name: str, query: str) -> tuple[str, str]:
            try:
                tool = TOOLS[tool_name]
                if tool_name == "rag":
                    from .tools import _retrieve_context
                    result = _retrieve_context(query, namespace=namespace)
                else:
                    result = await tool.run(query)
                return tool_name, result
            except Exception as e:
                return tool_name, f"Error: {str(e)}"
        
        # Execute all tools in parallel
        tasks = [run_tool(tool_name, query) for tool_name, query in tool_queries.items()]
        results_list = await asyncio.gather(*tasks)
        
        return dict(results_list)


# Global tool chain instance
tool_chain = ToolChain()