"""Document processing utilities for AgentKit."""

import io
import os
from typing import Dict, List, Optional, Union
from pathlib import Path

try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DocumentProcessor:
    """Process various document formats and extract text content."""

    SUPPORTED_FORMATS = {
        "text/plain": "txt",
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/markdown": "md",
        "text/csv": "csv",
        "application/json": "json",
    }

    @classmethod
    def is_supported(cls, content_type: str) -> bool:
        """Check if file type is supported."""
        return content_type in cls.SUPPORTED_FORMATS

    @classmethod
    def get_missing_dependencies(cls) -> List[str]:
        """Get list of missing optional dependencies."""
        missing = []
        if not PDF_AVAILABLE:
            missing.append("PyPDF2")
        if not DOCX_AVAILABLE:
            missing.append("python-docx")
        return missing

    @classmethod
    async def process_file(
        cls, content: bytes, filename: str, content_type: str
    ) -> Dict[str, Union[str, int, bool]]:
        """
        Process uploaded file and extract text content.

        Returns:
            Dict with extracted text, metadata, and processing info
        """
        result = {
            "filename": filename,
            "content_type": content_type,
            "size": len(content),
            "text_content": "",
            "page_count": 0,
            "word_count": 0,
            "processing_success": False,
            "error_message": None,
        }

        try:
            if content_type == "text/plain":
                result["text_content"] = content.decode("utf-8", errors="ignore")
                result["processing_success"] = True

            elif content_type == "application/pdf" and PDF_AVAILABLE:
                result.update(await cls._process_pdf(content))

            elif (
                content_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                and DOCX_AVAILABLE
            ):
                result.update(await cls._process_docx(content))

            elif content_type in ["text/markdown", "text/csv", "application/json"]:
                result["text_content"] = content.decode("utf-8", errors="ignore")
                result["processing_success"] = True

            else:
                result["error_message"] = f"Unsupported file type: {content_type}"

            # Calculate word count if text was extracted
            if result["text_content"]:
                result["word_count"] = len(result["text_content"].split())

        except Exception as e:
            result["error_message"] = f"Error processing file: {str(e)}"

        return result

    @classmethod
    async def _process_pdf(cls, content: bytes) -> Dict[str, Union[str, int, bool]]:
        """Extract text from PDF file."""
        if not PDF_AVAILABLE:
            return {
                "text_content": "",
                "processing_success": False,
                "error_message": "PyPDF2 not installed. Run: pip install PyPDF2",
            }

        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n\n"

            return {
                "text_content": text_content.strip(),
                "page_count": len(pdf_reader.pages),
                "processing_success": True,
            }

        except Exception as e:
            return {
                "text_content": "",
                "processing_success": False,
                "error_message": f"PDF processing error: {str(e)}",
            }

    @classmethod
    async def _process_docx(cls, content: bytes) -> Dict[str, Union[str, int, bool]]:
        """Extract text from DOCX file."""
        if not DOCX_AVAILABLE:
            return {
                "text_content": "",
                "processing_success": False,
                "error_message": "python-docx not installed. Run: pip install python-docx",
            }

        try:
            docx_file = io.BytesIO(content)
            doc = docx.Document(docx_file)

            text_content = ""
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"

            return {"text_content": text_content.strip(), "processing_success": True}

        except Exception as e:
            return {
                "text_content": "",
                "processing_success": False,
                "error_message": f"DOCX processing error: {str(e)}",
            }

    @classmethod
    def create_document_summary(cls, processed_files: List[Dict]) -> str:
        """Create a summary of processed documents for the AI agent."""
        if not processed_files:
            return ""

        summary_parts = ["📎 **Uploaded Documents:**"]

        for file_info in processed_files:
            filename = file_info["filename"]
            size_kb = file_info["size"] / 1024

            if file_info["processing_success"]:
                word_count = file_info.get("word_count", 0)
                page_count = file_info.get("page_count", 0)

                summary_parts.append(
                    f"- **{filename}** ({size_kb:.1f}KB, {word_count} words"
                    + (f", {page_count} pages" if page_count > 0 else "")
                    + ")"
                )

                # Add content preview (first 200 chars)
                content = file_info.get("text_content", "")
                if content:
                    preview = content[:200].replace("\n", " ")
                    if len(content) > 200:
                        preview += "..."
                    summary_parts.append(f"  *Preview:* {preview}")
            else:
                error = file_info.get("error_message", "Unknown error")
                summary_parts.append(f"- **{filename}** (⚠️ Error: {error})")

        return "\n".join(summary_parts)
