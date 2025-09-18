"""
Basic tests for AgentKit backend functionality.
Run with: python -m pytest
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app, MAX_FILE_SIZE, CONVERSATION_HISTORY_LIMIT

client = TestClient(app)


class TestAPI:
    """Test AgentKit API endpoints."""

    def test_health_check(self):
        """Test if the API is running."""
        # Test root endpoint exists
        response = client.get("/")
        # Should return 404 for root since we don't have a root endpoint
        assert response.status_code == 404

    def test_models_endpoint(self):
        """Test models endpoint returns available models."""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert "available_models" in data
        assert "default_model" in data
        assert isinstance(data["available_models"], list)
        assert len(data["available_models"]) > 0

    def test_files_endpoint(self):
        """Test files listing endpoint."""
        response = client.get("/files")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert isinstance(data["files"], list)

    @patch("agent.agent.run_agent_with_history")
    async def test_chat_endpoint_basic(self, mock_agent):
        """Test basic chat functionality."""
        mock_agent.return_value = {
            "answer": "Test response",
            "tool_used": "idle",
            "tool_output": "",
            "model": "gemini-2.0-flash-001",
            "context": "",
            "summary": "",
        }

        response = client.post(
            "/chat",
            data={
                "message": "Hello test",
                "model": "gemini-2.0-flash-001",
                "history": "[]",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_chat_endpoint_missing_params(self):
        """Test chat endpoint with missing parameters."""
        response = client.post("/chat", data={})
        assert response.status_code == 422  # Validation error


class TestConfiguration:
    """Test configuration and environment variables."""

    def test_max_file_size_configuration(self):
        """Test that MAX_FILE_SIZE is properly configured."""
        assert isinstance(MAX_FILE_SIZE, int)
        assert MAX_FILE_SIZE > 0

    def test_conversation_history_limit(self):
        """Test that CONVERSATION_HISTORY_LIMIT is properly configured."""
        assert isinstance(CONVERSATION_HISTORY_LIMIT, int)
        assert CONVERSATION_HISTORY_LIMIT > 0

    def test_environment_variables(self):
        """Test that environment variables can be loaded."""
        # These might not be set in test environment, but should not crash
        google_key = os.getenv("GOOGLE_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")

        # Should be strings or None, not crash
        assert google_key is None or isinstance(google_key, str)
        assert tavily_key is None or isinstance(tavily_key, str)


class TestFileUpload:
    """Test file upload functionality."""

    def test_file_size_limit_validation(self):
        """Test that file size limits are enforced."""
        # Create a mock file that's too large
        large_content = b"x" * (MAX_FILE_SIZE + 1)

        response = client.post(
            "/chat",
            data={
                "message": "Test with large file",
                "model": "gemini-2.0-flash-001",
                "history": "[]",
            },
            files={"files": ("large_file.txt", large_content, "text/plain")},
        )
        assert response.status_code == 413  # File too large


if __name__ == "__main__":
    pytest.main([__file__])
