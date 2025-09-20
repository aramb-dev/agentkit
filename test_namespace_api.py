"""
Tests for namespace management functionality.
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)


class TestNamespaceAPI:
    """Test namespace management API endpoints."""

    def test_list_namespaces_empty(self):
        """Test listing namespaces when no collections exist."""
        with patch('app.main.list_collections', return_value=[]):
            response = client.get("/namespaces")
            assert response.status_code == 200
            data = response.json()
            assert "namespaces" in data
            assert "total" in data
            # Should still include default namespace
            assert len(data["namespaces"]) >= 1
            assert any(ns["name"] == "default" for ns in data["namespaces"])

    def test_list_namespaces_with_collections(self):
        """Test listing namespaces with existing collections."""
        mock_collections = ["default", "project1", "research"]
        with patch('app.main.list_collections', return_value=mock_collections), \
             patch('app.main.get_collection') as mock_get_collection:
            
            # Mock collection count
            mock_collection = Mock()
            mock_collection.count.return_value = 5
            mock_get_collection.return_value = mock_collection
            
            response = client.get("/namespaces")
            assert response.status_code == 200
            data = response.json()
            assert len(data["namespaces"]) == 3
            
            # Check default namespace properties
            default_ns = next(ns for ns in data["namespaces"] if ns["name"] == "default")
            assert default_ns["is_default"] is True
            assert default_ns["document_count"] == 5

    def test_create_namespace_success(self):
        """Test successful namespace creation."""
        with patch('app.main.list_collections', return_value=["default"]), \
             patch('app.main.get_collection') as mock_get_collection:
            
            response = client.post("/namespaces", data={"name": "new-project"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["namespace"] == "new-project"
            mock_get_collection.assert_called_with("new-project")

    def test_create_namespace_invalid_name(self):
        """Test namespace creation with invalid name."""
        test_cases = [
            "",  # Empty name
            "  ",  # Whitespace only
            "invalid@name",  # Invalid characters
            "name with spaces",  # Spaces
        ]
        
        for invalid_name in test_cases:
            response = client.post("/namespaces", data={"name": invalid_name})
            assert response.status_code == 400

    def test_create_namespace_already_exists(self):
        """Test creating namespace that already exists."""
        with patch('app.main.list_collections', return_value=["default", "existing"]):
            response = client.post("/namespaces", data={"name": "existing"})
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"]

    def test_delete_namespace_success(self):
        """Test successful namespace deletion."""
        with patch('app.main.list_collections', return_value=["default", "to-delete"]), \
             patch('app.main.delete_namespace') as mock_delete:
            
            response = client.delete("/namespaces/to-delete")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            mock_delete.assert_called_with("to-delete")

    def test_delete_default_namespace_forbidden(self):
        """Test that default namespace cannot be deleted."""
        response = client.delete("/namespaces/default")
        assert response.status_code == 400
        assert "Cannot delete the default namespace" in response.json()["detail"]

    def test_delete_nonexistent_namespace(self):
        """Test deleting a namespace that doesn't exist."""
        with patch('app.main.list_collections', return_value=["default"]):
            response = client.delete("/namespaces/nonexistent")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_rename_namespace_success(self):
        """Test successful namespace renaming."""
        with patch('app.main.list_collections', return_value=["default", "old-name"]), \
             patch('app.main.get_collection') as mock_get_collection, \
             patch('app.main.delete_namespace') as mock_delete:
            
            # Mock collection with documents
            mock_collection = Mock()
            mock_collection.get.return_value = {
                "ids": ["id1", "id2"],
                "embeddings": [[[0.1, 0.2]], [[0.3, 0.4]]],
                "metadatas": [{"test": "data1"}, {"test": "data2"}],
                "documents": ["doc1", "doc2"]
            }
            mock_get_collection.return_value = mock_collection
            
            response = client.put("/namespaces/old-name/rename", data={"new_name": "new-name"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["old_name"] == "old-name"
            assert data["new_name"] == "new-name"

    def test_rename_default_namespace_forbidden(self):
        """Test that default namespace cannot be renamed."""
        response = client.put("/namespaces/default/rename", data={"new_name": "new-default"})
        assert response.status_code == 400
        assert "Cannot rename the default namespace" in response.json()["detail"]

    def test_rename_namespace_invalid_new_name(self):
        """Test renaming with invalid new name."""
        with patch('app.main.list_collections', return_value=["default", "old-name"]):
            response = client.put("/namespaces/old-name/rename", data={"new_name": "invalid@name"})
            assert response.status_code == 400

    def test_rename_namespace_name_exists(self):
        """Test renaming to a name that already exists."""
        with patch('app.main.list_collections', return_value=["default", "old-name", "existing"]):
            response = client.put("/namespaces/old-name/rename", data={"new_name": "existing"})
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"]

    def test_list_namespace_documents_empty(self):
        """Test listing documents in empty namespace."""
        with patch('app.main.list_collections', return_value=["default", "test-namespace"]), \
             patch('app.main.get_collection') as mock_get_collection:
            
            # Mock empty collection
            mock_collection = Mock()
            mock_collection.get.return_value = {"metadatas": []}
            mock_get_collection.return_value = mock_collection
            
            response = client.get("/namespaces/test-namespace/documents")
            assert response.status_code == 200
            data = response.json()
            assert data["namespace"] == "test-namespace"
            assert data["documents"] == []
            assert data["total_documents"] == 0

    def test_list_namespace_documents_with_docs(self):
        """Test listing documents in namespace with documents."""
        with patch('app.main.list_collections', return_value=["default", "test-namespace"]), \
             patch('app.main.get_collection') as mock_get_collection:
            
            # Mock collection with documents
            mock_collection = Mock()
            mock_collection.get.return_value = {
                "metadatas": [
                    {"doc_id": "doc1", "filename": "test1.pdf", "session_id": "session1"},
                    {"doc_id": "doc1", "filename": "test1.pdf", "session_id": "session1"},  # Same doc, different chunk
                    {"doc_id": "doc2", "filename": "test2.pdf", "session_id": "session2"},
                ],
                "ids": ["chunk1", "chunk2", "chunk3"]
            }
            mock_get_collection.return_value = mock_collection
            
            response = client.get("/namespaces/test-namespace/documents")
            assert response.status_code == 200
            data = response.json()
            assert data["namespace"] == "test-namespace"
            assert len(data["documents"]) == 2  # Two unique documents
            assert data["total_documents"] == 2
            assert data["total_chunks"] == 3

    def test_list_namespace_documents_nonexistent(self):
        """Test listing documents in nonexistent namespace."""
        with patch('app.main.list_collections', return_value=["default"]):
            response = client.get("/namespaces/nonexistent/documents")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])