from typing import List, Dict
from pypdf import PdfReader
import uuid
import re
from pathlib import Path

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file."""
    reader = PdfReader(file_path)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            texts.append("")
    return "\n".join(texts)


def extract_text_from_docx(file_path: str) -> str:
    """Extract text content from a DOCX file."""
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx not installed. Run: pip install python-docx")
    
    doc = docx.Document(file_path)
    texts = []
    for paragraph in doc.paragraphs:
        texts.append(paragraph.text)
    return "\n".join(texts)


def extract_text_from_txt(file_path: str) -> str:
    """Extract text content from a TXT file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def extract_text_from_md(file_path: str) -> str:
    """Extract text content from a Markdown file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def extract_text_from_file(file_path: str) -> str:
    """Extract text from a file based on its extension."""
    path = Path(file_path)
    extension = path.suffix.lower()
    
    if extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif extension == '.docx':
        return extract_text_from_docx(file_path)
    elif extension == '.txt':
        return extract_text_from_txt(file_path)
    elif extension in ['.md', '.markdown']:
        return extract_text_from_md(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks for better retrieval."""
    # Simple sentence-ish splitter then window
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, cur, cur_len = [], [], 0

    for s in sentences:
        if cur_len + len(s) > chunk_size and cur:
            chunks.append(" ".join(cur))
            # Add overlap
            overlap_tokens = (
                " ".join(" ".join(cur).split()[-overlap:]) if overlap else ""
            )
            cur = [overlap_tokens, s] if overlap_tokens else [s]
            cur_len = len(" ".join(cur))
        else:
            cur.append(s)
            cur_len += len(s)

    if cur:
        chunks.append(" ".join(cur))

    # Filter empty/short chunks
    return [c.strip() for c in chunks if len(c.strip()) > 30]


def build_doc_chunks(file_path: str, metadata: Dict) -> List[Dict]:
    """Extract text from document and build document chunks with metadata."""
    text = extract_text_from_file(file_path)
    chunks = chunk_text(text)
    doc_id = metadata.get("doc_id") or str(uuid.uuid4())

    results = []
    for i, ch in enumerate(chunks):
        results.append(
            {"id": f"{doc_id}-{i}", "text": ch, "metadata": {**metadata, "chunk": i}}
        )

    return results
