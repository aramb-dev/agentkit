"""
Tests for conversation persistence functionality.
Run with: python -m pytest test_conversations.py -v
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock
import uuid
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app import database as db

client = TestClient(app)


class TestConversationPersistence:
    """Test conversation persistence functionality."""

    def setup_method(self):
        """Setup for each test - clean database."""
        # Note: In a real scenario, we'd use a test database
        # For now, we'll work with the existing database
        pass

    def test_create_conversation_via_chat(self):
        """Test that conversations are created automatically via chat."""
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "Test response",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            session_id = f"test-session-{uuid.uuid4()}"
            
            response = client.post(
                "/chat",
                data={
                    "message": "Hello, create a conversation",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id,
                    "namespace": "test"
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "conversation_id" in data
            
            # Verify conversation was created
            conversation = db.get_conversation_by_session(session_id)
            assert conversation is not None
            assert conversation["session_id"] == session_id
            assert conversation["namespace"] == "test"

    def test_list_conversations(self):
        """Test listing conversations."""
        response = client.get("/conversations")
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data
        assert isinstance(data["conversations"], list)

    def test_list_conversations_with_pagination(self):
        """Test listing conversations with pagination."""
        response = client.get("/conversations?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_get_conversation_detail(self):
        """Test getting conversation details."""
        # First create a conversation via chat
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "Test response",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            session_id = f"test-detail-{uuid.uuid4()}"
            
            chat_response = client.post(
                "/chat",
                data={
                    "message": "Test message for detail",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id,
                },
            )
            
            conversation_id = chat_response.json()["conversation_id"]
            
            # Now get the conversation detail
            response = client.get(f"/conversations/{conversation_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == conversation_id
            assert "messages" in data
            assert len(data["messages"]) >= 2  # At least user and assistant messages

    def test_get_nonexistent_conversation(self):
        """Test getting a conversation that doesn't exist."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/conversations/{fake_id}")
        assert response.status_code == 404

    def test_update_conversation_title(self):
        """Test updating conversation title."""
        # First create a conversation
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "Test response",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            session_id = f"test-update-{uuid.uuid4()}"
            
            chat_response = client.post(
                "/chat",
                data={
                    "message": "Test for update",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id,
                },
            )
            
            conversation_id = chat_response.json()["conversation_id"]
            
            # Update the title
            new_title = "Updated Conversation Title"
            response = client.put(
                f"/conversations/{conversation_id}",
                params={"title": new_title}
            )
            assert response.status_code == 200
            assert response.json()["success"] is True
            
            # Verify the update
            get_response = client.get(f"/conversations/{conversation_id}")
            assert get_response.json()["title"] == new_title

    def test_delete_conversation(self):
        """Test deleting a conversation."""
        # First create a conversation
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "Test response",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            session_id = f"test-delete-{uuid.uuid4()}"
            
            chat_response = client.post(
                "/chat",
                data={
                    "message": "Test for deletion",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id,
                },
            )
            
            conversation_id = chat_response.json()["conversation_id"]
            
            # Delete the conversation
            response = client.delete(f"/conversations/{conversation_id}")
            assert response.status_code == 200
            assert response.json()["success"] is True
            
            # Verify it's deleted
            get_response = client.get(f"/conversations/{conversation_id}")
            assert get_response.status_code == 404

    def test_search_messages(self):
        """Test searching messages."""
        # Create a conversation with specific content
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "This is a searchable response about Python",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            session_id = f"test-search-{uuid.uuid4()}"
            
            client.post(
                "/chat",
                data={
                    "message": "Tell me about Python programming",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id,
                },
            )
            
            # Search for messages
            response = client.get("/conversations/search/messages?query=Python")
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            # Should find at least our test message
            found = any("Python" in msg["content"] for msg in data["messages"])
            assert found

    def test_export_conversation_json(self):
        """Test exporting conversation as JSON."""
        # Create a conversation
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "Export test response",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            session_id = f"test-export-{uuid.uuid4()}"
            
            chat_response = client.post(
                "/chat",
                data={
                    "message": "Test export",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id,
                },
            )
            
            conversation_id = chat_response.json()["conversation_id"]
            
            # Export as JSON
            response = client.post(f"/conversations/{conversation_id}/export?format=json")
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert data["id"] == conversation_id

    def test_export_conversation_txt(self):
        """Test exporting conversation as text."""
        # Create a conversation
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "Export test response",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            session_id = f"test-export-txt-{uuid.uuid4()}"
            
            chat_response = client.post(
                "/chat",
                data={
                    "message": "Test export txt",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id,
                },
            )
            
            conversation_id = chat_response.json()["conversation_id"]
            
            # Export as text
            response = client.post(f"/conversations/{conversation_id}/export?format=txt")
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert data["format"] == "txt"
            assert "USER:" in data["content"]
            assert "ASSISTANT:" in data["content"]

    def test_export_conversation_md(self):
        """Test exporting conversation as markdown."""
        # Create a conversation
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "Export test response",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            session_id = f"test-export-md-{uuid.uuid4()}"
            
            chat_response = client.post(
                "/chat",
                data={
                    "message": "Test export markdown",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id,
                },
            )
            
            conversation_id = chat_response.json()["conversation_id"]
            
            # Export as markdown
            response = client.post(f"/conversations/{conversation_id}/export?format=md")
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert data["format"] == "md"
            assert "### 👤 User" in data["content"]
            assert "### 🤖 Assistant" in data["content"]

    def test_conversation_namespace_filtering(self):
        """Test filtering conversations by namespace."""
        # Create conversations in different namespaces
        with patch("agent.agent.run_agent_with_history") as mock_agent:
            mock_agent.return_value = {
                "answer": "Test response",
                "tool_used": "idle",
                "tool_output": "",
                "model": "gemini-2.0-flash-001",
                "context": "",
                "summary": "",
            }

            # Create in test-ns-1
            session_id_1 = f"test-ns-1-{uuid.uuid4()}"
            client.post(
                "/chat",
                data={
                    "message": "Test namespace 1",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id_1,
                    "namespace": "test-ns-1"
                },
            )
            
            # Create in test-ns-2
            session_id_2 = f"test-ns-2-{uuid.uuid4()}"
            client.post(
                "/chat",
                data={
                    "message": "Test namespace 2",
                    "model": "gemini-2.0-flash-001",
                    "history": "[]",
                    "session_id": session_id_2,
                    "namespace": "test-ns-2"
                },
            )
            
            # Filter by namespace
            response = client.get("/conversations?namespace=test-ns-1")
            assert response.status_code == 200
            data = response.json()
            # Should only have conversations from test-ns-1
            for conv in data["conversations"]:
                if conv["session_id"] == session_id_1:
                    assert conv["namespace"] == "test-ns-1"


class TestDatabaseModule:
    """Test database module directly."""

    def test_create_and_get_conversation(self):
        """Test creating and retrieving a conversation."""
        conv_id = str(uuid.uuid4())
        session_id = f"db-test-{uuid.uuid4()}"
        
        # Create conversation
        conversation = db.create_conversation(
            conversation_id=conv_id,
            session_id=session_id,
            title="Test Conversation",
            namespace="test"
        )
        
        assert conversation["id"] == conv_id
        assert conversation["session_id"] == session_id
        assert conversation["title"] == "Test Conversation"
        
        # Retrieve it
        retrieved = db.get_conversation(conv_id)
        assert retrieved is not None
        assert retrieved["id"] == conv_id
        
        # Cleanup
        db.delete_conversation(conv_id)

    def test_add_and_get_messages(self):
        """Test adding and retrieving messages."""
        conv_id = str(uuid.uuid4())
        session_id = f"db-msg-test-{uuid.uuid4()}"
        
        # Create conversation
        db.create_conversation(
            conversation_id=conv_id,
            session_id=session_id,
            title="Test Messages"
        )
        
        # Add messages
        msg_id_1 = str(uuid.uuid4())
        db.add_message(
            message_id=msg_id_1,
            conversation_id=conv_id,
            role="user",
            content="Hello"
        )
        
        msg_id_2 = str(uuid.uuid4())
        db.add_message(
            message_id=msg_id_2,
            conversation_id=conv_id,
            role="assistant",
            content="Hi there",
            model="gemini-2.0-flash-001"
        )
        
        # Retrieve messages
        messages = db.get_messages(conv_id)
        assert len(messages) == 2
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi there"
        
        # Cleanup
        db.delete_conversation(conv_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
