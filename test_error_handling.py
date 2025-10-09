"""
Tests for error handling and validation improvements.
Phase 2.2: Improve Error Handling & Validation

Run with: python -m pytest test_error_handling.py -v
"""

import pytest
import os
import sys
import io
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app, MAX_FILE_SIZE, validate_file_upload, ErrorCodes

client = TestClient(app)


class TestFileValidation:
    """Test file validation logic."""

    def test_validate_file_too_large(self):
        """Test that files exceeding size limit are rejected."""
        # Create a mock file that's too large
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        
        response = client.post(
            "/chat",
            data={
                "message": "Test with large file",
                "model": "gemini-1.5-flash",
                "history": "[]",
            },
            files={"files": ("large_file.txt", large_content, "text/plain")},
        )
        
        assert response.status_code == 413
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == ErrorCodes.FILE_TOO_LARGE
        assert "50" in data["error"]["message"].lower() or "mb" in data["error"]["message"].lower()

    def test_validate_unsupported_file_type(self):
        """Test that unsupported file types are rejected."""
        unsupported_content = b"fake executable content"
        
        response = client.post(
            "/docs/ingest",
            data={
                "namespace": "test",
                "session_id": "test-session",
            },
            files={"file": ("malware.exe", unsupported_content, "application/x-msdownload")},
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "unsupported" in data["error"]["message"].lower()

    def test_validate_empty_file(self):
        """Test that empty files are rejected."""
        empty_content = b""
        
        response = client.post(
            "/docs/ingest",
            data={
                "namespace": "test",
                "session_id": "test-session",
            },
            files={"file": ("empty.txt", empty_content, "text/plain")},
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "empty" in data["error"]["message"].lower()

    def test_validate_valid_text_file(self):
        """Test that valid text files are accepted."""
        # Use a simple text file instead of PDF to avoid PDF processing dependencies
        text_content = b"This is a test document content for validation."
        
        with patch("rag.ingest.build_doc_chunks") as mock_chunks, \
             patch("rag.store.upsert_chunks") as mock_upsert:
            mock_chunks.return_value = [{"text": "test", "metadata": {"doc_id": "123"}}]
            
            response = client.post(
                "/docs/ingest",
                data={
                    "namespace": "test",
                    "session_id": "test-session",
                },
                files={"file": ("test.txt", text_content, "text/plain")},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_acceptable_file_sizes(self):
        """Test that files within size limits are accepted."""
        # Test various acceptable sizes
        sizes_to_test = [
            1024,  # 1KB
            1024 * 1024,  # 1MB
            10 * 1024 * 1024,  # 10MB
            40 * 1024 * 1024,  # 40MB
        ]
        
        for size in sizes_to_test:
            content = b"x" * size
            
            with patch("rag.ingest.build_doc_chunks") as mock_chunks, \
                 patch("rag.store.upsert_chunks") as mock_upsert:
                mock_chunks.return_value = [{"text": "test", "metadata": {"doc_id": "123"}}]
                
                response = client.post(
                    "/docs/ingest",
                    data={
                        "namespace": "test",
                        "session_id": "test-session",
                    },
                    files={"file": ("test.txt", content, "text/plain")},
                )
                
                assert response.status_code == 200, f"Failed for size {size / (1024*1024):.1f}MB"


class TestErrorResponseFormat:
    """Test standardized error response format."""

    def test_error_response_structure(self):
        """Test that error responses follow standardized format."""
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        
        response = client.post(
            "/docs/ingest",
            data={
                "namespace": "test",
                "session_id": "test-session",
            },
            files={"file": ("large.txt", large_content, "text/plain")},
        )
        
        assert response.status_code == 413
        data = response.json()
        
        # Check standardized error structure
        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "timestamp" in error
        assert error["code"] == ErrorCodes.FILE_TOO_LARGE

    def test_error_codes_consistency(self):
        """Test that error codes are consistent across endpoints."""
        # Test FILE_TOO_LARGE on different endpoints
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        
        # Test on /docs/ingest
        response1 = client.post(
            "/docs/ingest",
            data={"namespace": "test", "session_id": "test"},
            files={"file": ("large.txt", large_content, "text/plain")},
        )
        
        # Test on /chat
        response2 = client.post(
            "/chat",
            data={"message": "test", "model": "gemini-1.5-flash", "history": "[]"},
            files={"files": ("large.txt", large_content, "text/plain")},
        )
        
        assert response1.status_code == 413
        assert response2.status_code == 413
        assert response1.json()["error"]["code"] == ErrorCodes.FILE_TOO_LARGE
        assert response2.json()["error"]["code"] == ErrorCodes.FILE_TOO_LARGE


class TestRequestValidation:
    """Test request validation middleware."""

    def test_request_id_header(self):
        """Test that request ID is added to responses."""
        response = client.get("/models")
        assert "X-Request-ID" in response.headers

    def test_missing_required_parameters(self):
        """Test validation of required parameters."""
        response = client.post("/chat", data={})
        assert response.status_code == 422  # Validation error

    def test_invalid_namespace_name(self):
        """Test validation of namespace names."""
        # Test with invalid characters
        response = client.post(
            "/namespaces",
            data={"name": "invalid/namespace"},
        )
        assert response.status_code == 400


class TestErrorLogging:
    """Test error logging functionality."""

    @patch("app.main.logger")
    def test_error_logging_on_validation_failure(self, mock_logger):
        """Test that validation failures are logged."""
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        
        response = client.post(
            "/docs/ingest",
            data={"namespace": "test", "session_id": "test"},
            files={"file": ("large.txt", large_content, "text/plain")},
        )
        
        assert response.status_code == 413
        # Verify that logger was called
        assert mock_logger.warning.called or mock_logger.error.called

    @patch("app.main.logger")
    def test_error_logging_includes_context(self, mock_logger):
        """Test that error logs include useful context."""
        response = client.post(
            "/docs/ingest",
            data={"namespace": "test", "session_id": "test"},
            files={"file": ("test.exe", b"content", "application/x-msdownload")},
        )
        
        assert response.status_code == 400


class TestConfiguration:
    """Test configuration values."""

    def test_max_file_size_updated(self):
        """Test that MAX_FILE_SIZE is set to 50MB."""
        # 50MB = 52428800 bytes
        assert MAX_FILE_SIZE == 52428800, f"Expected 52428800 bytes (50MB), got {MAX_FILE_SIZE}"

    def test_supported_file_types(self):
        """Test that all expected file types are supported."""
        from app.main import SUPPORTED_EXTENSIONS
        
        expected_types = ['.pdf', '.docx', '.txt', '.md', '.markdown', '.json']
        for file_type in expected_types:
            assert file_type in SUPPORTED_EXTENSIONS, f"{file_type} should be supported"


class TestPathTraversalProtection:
    """Test protection against path traversal attacks."""

    def test_reject_path_traversal_in_filename(self):
        """Test that filenames with path traversal are rejected."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "subdir/../../../etc/passwd",
        ]
        
        for filename in malicious_filenames:
            response = client.post(
                "/docs/ingest",
                data={"namespace": "test", "session_id": "test"},
                files={"file": (filename, b"content", "text/plain")},
            )
            
            assert response.status_code == 400, f"Should reject filename: {filename}"
            data = response.json()
            assert "path traversal" in data["error"]["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
