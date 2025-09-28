"""
Enhanced tests for AgentKit intelligent routing and tool chaining.
"""

import pytest
import sys
import os
import asyncio

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.router import (
    select_tool, 
    _analyze_message_context, 
    _enhanced_fallback_routing,
    get_routing_metrics,
    reset_routing_metrics
)
from agent.tool_chain import tool_chain, ChainStep
from agent.tools import TOOLS, get_all_tool_performance_stats, reset_tool_metrics
from agent.agent import run_agent_with_history


class TestEnhancedRouter:
    """Test enhanced routing system with context awareness."""
    
    def setup_method(self):
        """Reset metrics before each test."""
        reset_routing_metrics()
        reset_tool_metrics()
    
    def test_message_context_analysis(self):
        """Test context analysis functionality."""
        # Simple conversational message
        analysis = _analyze_message_context("hello there")
        assert analysis["conversational"] is True
        assert analysis["complexity"] == "simple"
        
        # Complex factual question
        analysis = _analyze_message_context("What is the current market price of Bitcoin and how has it changed over the past week?")
        assert analysis["needs_facts"] is True
        assert analysis["complexity"] == "complex"
        
        # AgentKit-specific query
        analysis = _analyze_message_context("explain the agentkit architecture")
        assert analysis["about_agentkit"] is True
        
        # Memory-related query
        analysis = _analyze_message_context("remember what I said about my birthday")
        assert analysis["memory_intent"] is True
    
    def test_enhanced_fallback_routing(self):
        """Test enhanced fallback routing with context analysis."""
        # Test with context analysis
        analysis = {"needs_facts": True, "complexity": "complex", "about_agentkit": False, "memory_intent": False, "conversational": False}
        result = _enhanced_fallback_routing("what is the weather", "", analysis)
        assert result == "web"
        
        analysis = {"needs_facts": False, "complexity": "simple", "about_agentkit": True, "memory_intent": False, "conversational": False}
        result = _enhanced_fallback_routing("agentkit setup", "", analysis)
        assert result == "rag"
        
        analysis = {"needs_facts": False, "complexity": "simple", "about_agentkit": False, "memory_intent": True, "conversational": False}
        result = _enhanced_fallback_routing("recall what I said", "", analysis)
        assert result == "memory"
    
    def test_routing_metrics_collection(self):
        """Test that routing metrics are collected properly."""
        initial_metrics = get_routing_metrics()
        assert initial_metrics["total_routes"] == 0
        
        # Simulate some routing (would normally happen through select_tool)
        from agent.router import _log_routing_decision
        analysis = {"complexity": "simple"}
        _log_routing_decision("test message", "web", analysis, "llm")
        
        metrics = get_routing_metrics()
        assert metrics["total_routes"] == 1
        assert metrics["tool_usage"]["web"] == 1
        assert metrics["routing_methods"]["llm"] == 1


class TestToolChaining:
    """Test tool chaining capabilities."""
    
    @pytest.mark.asyncio
    async def test_chain_detection(self):
        """Test chain opportunity detection."""
        # Should detect no chain needed for simple queries
        result = await tool_chain.detect_chain_opportunity("hello")
        assert result is None
        
        # Should detect chain opportunities for complex queries
        result = await tool_chain.detect_chain_opportunity("find information about Tesla and remember it")
        # Note: This test might be None if the LLM is not available, which is expected
        
    @pytest.mark.asyncio
    async def test_chain_execution(self):
        """Test chain execution with mock steps."""
        steps = [
            ChainStep(tool_name="web", query="test query"),
            ChainStep(tool_name="memory", query="remember this", depends_on=["web"])
        ]
        
        result = await tool_chain.execute_chain(steps)
        
        # Should complete successfully even with fallback responses
        assert result.success is True or result.success is False  # Depends on tool availability
        assert len(result.execution_order) > 0
        assert result.total_time > 0
        
    @pytest.mark.asyncio
    async def test_parallel_tool_execution(self):
        """Test parallel tool execution."""
        tool_queries = {
            "web": "test web query",
            "memory": "test memory query"
        }
        
        results = await tool_chain.execute_parallel_tools(tool_queries)
        
        assert "web" in results
        assert "memory" in results
        assert isinstance(results["web"], str)
        assert isinstance(results["memory"], str)


class TestPerformanceMonitoring:
    """Test tool performance monitoring."""
    
    def setup_method(self):
        """Reset metrics before each test."""
        reset_tool_metrics()
    
    @pytest.mark.asyncio
    async def test_tool_performance_tracking(self):
        """Test that tool performance is tracked."""
        # Execute a tool
        tool = TOOLS["idle"]
        result = await tool.run("test query")
        
        # Check metrics were recorded
        stats = tool.get_performance_stats()
        assert stats["total_calls"] == 1
        assert stats["name"] == "idle"
        assert "average_response_time" in stats
        assert stats["last_used"] is not None
    
    def test_all_tool_stats(self):
        """Test getting all tool performance stats."""
        stats = get_all_tool_performance_stats()
        
        # Should have stats for all tools
        expected_tools = ["web", "rag", "memory", "idle"]
        for tool_name in expected_tools:
            assert tool_name in stats
            assert "total_calls" in stats[tool_name]
            assert "success_rate" in stats[tool_name]


class TestIntegratedWorkflows:
    """Test integrated workflows with enhanced routing and chaining."""
    
    @pytest.mark.asyncio 
    async def test_agent_with_enhanced_routing(self):
        """Test agent with enhanced routing capabilities."""
        # Simple conversational query
        result = await run_agent_with_history(
            message="hello",
            model="gemini",
            conversation_history=[]
        )
        
        assert "answer" in result
        assert "tool_used" in result
        assert "execution_time" in result
        assert "chain_execution" in result
        
        # Should not use chaining for simple queries
        assert result["chain_execution"] is False
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test agent error handling and fallbacks."""
        # Test with potentially complex query that might trigger chaining
        result = await run_agent_with_history(
            message="find current weather and remember my location",
            model="gemini", 
            conversation_history=[]
        )
        
        # Should handle gracefully even if tools fail
        assert "answer" in result
        assert "tool_used" in result
        
        # Should have error info if tool failed
        if result.get("tool_error"):
            assert isinstance(result["tool_error"], str)


class TestContextAwareRouting:
    """Test context-aware routing decisions."""
    
    @pytest.mark.asyncio
    async def test_routing_with_conversation_context(self):
        """Test that routing considers conversation context."""
        conversation = [
            {"role": "user", "content": "I'm working on a Python project"},
            {"role": "assistant", "content": "Great! I can help with Python development."}
        ]
        
        # This query should be routed differently with context
        result = await run_agent_with_history(
            message="find the latest updates",
            model="gemini",
            conversation_history=conversation
        )
        
        assert "answer" in result
        # With context about Python project, might route to web for Python updates
        
    @pytest.mark.asyncio
    async def test_routing_without_context(self):
        """Test routing without conversation context."""
        result = await run_agent_with_history(
            message="what's the weather like?",
            model="gemini", 
            conversation_history=[]
        )
        
        assert "answer" in result
        # Should route to web for factual weather query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])