"""
Tests for AgentKit agent functionality.
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.router import select_tool, _fallback_keyword_routing
from agent.llm_client import LLMClient
from agent.tools import TOOLS


class TestRouter:
    """Test the intelligent routing system."""

    def test_fallback_keyword_routing(self):
        """Test keyword-based routing fallback."""
        # Web search queries
        assert _fallback_keyword_routing("search for python tutorials") == "web"
        assert _fallback_keyword_routing("what is the latest news") == "web"
        assert _fallback_keyword_routing("who is the president") == "web"

        # AgentKit documentation queries
        assert _fallback_keyword_routing("explain agentkit architecture") == "rag"
        assert _fallback_keyword_routing("how does agentkit work") == "rag"

        # Memory queries
        assert _fallback_keyword_routing("remember my birthday") == "memory"
        assert _fallback_keyword_routing("recall what I said") == "memory"

        # General conversation
        assert _fallback_keyword_routing("hello") == "idle"
        assert _fallback_keyword_routing("thank you") == "idle"

    def test_tools_exist(self):
        """Test that all expected tools are available."""
        expected_tools = ["web", "rag", "memory", "idle"]
        for tool_name in expected_tools:
            assert tool_name in TOOLS
            assert hasattr(TOOLS[tool_name], "run")
            assert hasattr(TOOLS[tool_name], "description")


class TestLLMClient:
    """Test LLM client functionality."""

    def test_llm_client_initialization(self):
        """Test that LLM client initializes properly."""
        client = LLMClient()
        assert client is not None
        assert hasattr(client, "available_models")
        assert hasattr(client, "get_default_model")

    def test_model_availability(self):
        """Test model availability checking."""
        client = LLMClient()

        # Should have some models available (even fallback ones)
        models = client.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0

        # Default model should be one of available models
        default_model = client.get_default_model()
        assert isinstance(default_model, str)
        assert len(default_model) > 0

    def test_fallback_response(self):
        """Test fallback response when API is unavailable."""
        client = LLMClient()
        fallback = client._fallback_response("test query")
        assert isinstance(fallback, str)
        assert len(fallback) > 0
        assert "unable to access" in fallback.lower()


class TestTools:
    """Test individual tool functionality."""

    @pytest.mark.asyncio
    async def test_tools_execute(self):
        """Test that tools can execute without crashing."""
        test_query = "test query"

        for tool_name, tool in TOOLS.items():
            try:
                result = await tool.run(test_query)
                assert isinstance(result, str)
                assert len(result) > 0
            except Exception as e:
                pytest.fail(f"Tool {tool_name} failed to execute: {e}")

    def test_tool_descriptions(self):
        """Test that all tools have meaningful descriptions."""
        for tool_name, tool in TOOLS.items():
            assert hasattr(tool, "description")
            assert isinstance(tool.description, str)
            assert len(tool.description) > 10  # Should be descriptive


if __name__ == "__main__":
    pytest.main([__file__])
