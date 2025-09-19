from typing import List, Dict
from pypdf import PdfReader
import uuid
import re


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
    """Extract text from PDF and build document chunks with metadata."""
    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)
    doc_id = metadata.get("doc_id") or str(uuid.uuid4())

    results = []
    for i, ch in enumerate(chunks):
        results.append(
            {"id": f"{doc_id}-{i}", "text": ch, "metadata": {**metadata, "chunk": i}}
        )

    return results
