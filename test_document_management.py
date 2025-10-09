"""
Tests for document management functionality.
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


class TestDocumentManagement:
    """Test document management API endpoints."""

    def test_delete_document_success(self):
        """Test deleting a document successfully."""
        namespace = "test-namespace"
        doc_id = "test-doc-123"
        
        with patch('app.main.list_collections', return_value=[namespace]), \
             patch('app.main.delete_document', return_value=5):
            
            response = client.delete(f"/namespaces/{namespace}/documents/{doc_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["doc_id"] == doc_id
            assert data["namespace"] == namespace
            assert data["deleted_chunks"] == 5

    def test_delete_document_not_found(self):
        """Test deleting a non-existent document."""
        namespace = "test-namespace"
        doc_id = "non-existent-doc"
        
        with patch('app.main.list_collections', return_value=[namespace]), \
             patch('app.main.delete_document', return_value=0):
            
            response = client.delete(f"/namespaces/{namespace}/documents/{doc_id}")
            assert response.status_code == 404
            response_json = response.json()
            # Check structured error response format
            assert "error" in response_json
            assert "not found" in response_json["error"]["message"].lower()

    def test_delete_document_namespace_not_found(self):
        """Test deleting a document from non-existent namespace."""
        namespace = "non-existent-namespace"
        doc_id = "test-doc-123"
        
        with patch('app.main.list_collections', return_value=["other-namespace"]):
            response = client.delete(f"/namespaces/{namespace}/documents/{doc_id}")
            assert response.status_code == 404
            response_json = response.json()
            # Check structured error response format
            assert "error" in response_json
            assert "namespace" in response_json["error"]["message"].lower()

    def test_delete_document_error(self):
        """Test error handling when deleting a document."""
        namespace = "test-namespace"
        doc_id = "test-doc-123"
        
        with patch('app.main.list_collections', return_value=[namespace]), \
             patch('app.main.delete_document', side_effect=Exception("Database error")):
            
            response = client.delete(f"/namespaces/{namespace}/documents/{doc_id}")
            assert response.status_code == 500
            response_json = response.json()
            # Check structured error response format
            assert "error" in response_json
            assert "message" in response_json["error"]

    def test_list_namespace_documents(self):
        """Test listing documents in a namespace."""
        namespace = "test-namespace"
        
        mock_collection = Mock()
        mock_collection.get.return_value = {
            "ids": ["chunk1", "chunk2", "chunk3"],
            "metadatas": [
                {"doc_id": "doc1", "filename": "test.pdf", "session_id": "session1"},
                {"doc_id": "doc1", "filename": "test.pdf", "session_id": "session1"},
                {"doc_id": "doc2", "filename": "other.pdf", "session_id": "session2"},
            ]
        }
        
        with patch('app.main.list_collections', return_value=[namespace]), \
             patch('app.main.get_collection', return_value=mock_collection):
            
            response = client.get(f"/namespaces/{namespace}/documents")
            assert response.status_code == 200
            data = response.json()
            assert data["namespace"] == namespace
            assert data["total_documents"] == 2
            assert data["total_chunks"] == 3
            assert len(data["documents"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
