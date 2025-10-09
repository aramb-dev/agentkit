"""
Tests for multi-format document ingestion.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from rag.ingest import extract_text_from_file, build_doc_chunks

client = TestClient(app)


class TestMultiFormatIngestion:
    """Test multi-format document ingestion functionality."""

    def test_pdf_file_accepted(self):
        """Test that PDF files are accepted."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"PDF content")
            tmp_path = tmp_file.name

        try:
            with open(tmp_path, "rb") as f:
                with patch('app.main.build_doc_chunks', return_value=[]), \
                     patch('app.main.upsert_chunks'):
                    response = client.post(
                        "/docs/ingest",
                        files={"file": ("test.pdf", f, "application/pdf")},
                        data={"namespace": "test", "session_id": "test"}
                    )
                    assert response.status_code == 200
        finally:
            os.unlink(tmp_path)

    def test_docx_file_accepted(self):
        """Test that DOCX files are accepted."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_file:
            tmp_file.write(b"DOCX content")
            tmp_path = tmp_file.name

        try:
            with open(tmp_path, "rb") as f:
                with patch('app.main.build_doc_chunks', return_value=[]), \
                     patch('app.main.upsert_chunks'):
                    response = client.post(
                        "/docs/ingest",
                        files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                        data={"namespace": "test", "session_id": "test"}
                    )
                    assert response.status_code == 200
        finally:
            os.unlink(tmp_path)

    def test_txt_file_accepted(self):
        """Test that TXT files are accepted."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"TXT content")
            tmp_path = tmp_file.name

        try:
            with open(tmp_path, "rb") as f:
                with patch('app.main.build_doc_chunks', return_value=[]), \
                     patch('app.main.upsert_chunks'):
                    response = client.post(
                        "/docs/ingest",
                        files={"file": ("test.txt", f, "text/plain")},
                        data={"namespace": "test", "session_id": "test"}
                    )
                    assert response.status_code == 200
        finally:
            os.unlink(tmp_path)

    def test_md_file_accepted(self):
        """Test that Markdown files are accepted."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp_file:
            tmp_file.write(b"# Markdown content")
            tmp_path = tmp_file.name

        try:
            with open(tmp_path, "rb") as f:
                with patch('app.main.build_doc_chunks', return_value=[]), \
                     patch('app.main.upsert_chunks'):
                    response = client.post(
                        "/docs/ingest",
                        files={"file": ("test.md", f, "text/markdown")},
                        data={"namespace": "test", "session_id": "test"}
                    )
                    assert response.status_code == 200
        finally:
            os.unlink(tmp_path)

    def test_unsupported_file_rejected(self):
        """Test that unsupported file formats are rejected."""
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp_file:
            tmp_file.write(b"EXE content")
            tmp_path = tmp_file.name

        try:
            with open(tmp_path, "rb") as f:
                response = client.post(
                    "/docs/ingest",
                    files={"file": ("test.exe", f, "application/x-msdownload")},
                    data={"namespace": "test", "session_id": "test"}
                )
                assert response.status_code == 400
                assert "Unsupported file format" in response.json()["detail"]
        finally:
            os.unlink(tmp_path)

    def test_file_too_large_rejected(self):
        """Test that files larger than 10MB are rejected."""
        # Create a large file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            # Write more than 10MB
            tmp_file.write(b"x" * (11 * 1024 * 1024))
            tmp_path = tmp_file.name

        try:
            with open(tmp_path, "rb") as f:
                response = client.post(
                    "/docs/ingest",
                    files={"file": ("large.txt", f, "text/plain")},
                    data={"namespace": "test", "session_id": "test"}
                )
                assert response.status_code == 413
                assert "too large" in response.json()["detail"].lower()
        finally:
            os.unlink(tmp_path)

    def test_txt_text_extraction(self):
        """Test text extraction from TXT files."""
        content = "This is a test text file.\nWith multiple lines.\n"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            extracted = extract_text_from_file(tmp_path)
            assert extracted == content
        finally:
            os.unlink(tmp_path)

    def test_md_text_extraction(self):
        """Test text extraction from Markdown files."""
        content = "# Header\n\nThis is **bold** text.\n"
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode='w') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            extracted = extract_text_from_file(tmp_path)
            assert extracted == content
        finally:
            os.unlink(tmp_path)

    def test_build_doc_chunks_with_txt(self):
        """Test building document chunks from TXT file."""
        content = "This is a test. " * 100  # Create content that will be chunked
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            metadata = {
                "filename": "test.txt",
                "namespace": "test",
                "session_id": "test-session",
                "doc_id": "test-doc-123"
            }
            chunks = build_doc_chunks(tmp_path, metadata)
            
            # Verify chunks were created
            assert len(chunks) > 0
            
            # Verify each chunk has required fields
            for chunk in chunks:
                assert "id" in chunk
                assert "text" in chunk
                assert "metadata" in chunk
                assert chunk["metadata"]["filename"] == "test.txt"
                assert chunk["metadata"]["namespace"] == "test"
                assert chunk["metadata"]["doc_id"] == "test-doc-123"
                
        finally:
            os.unlink(tmp_path)

    def test_extract_unsupported_extension_raises_error(self):
        """Test that unsupported file extensions raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as tmp_file:
            tmp_file.write(b"content")
            tmp_path = tmp_file.name

        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                extract_text_from_file(tmp_path)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
