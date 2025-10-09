# RAG Integration Guide

## Overview

AgentKit includes a fully integrated RAG (Retrieval-Augmented Generation) system that enables document-based question answering with citations. This guide covers the complete integration from setup to production use.

## ✅ Integration Status

All acceptance criteria have been met:

- ✅ **RAG tool connected to actual vector store**: Uses ChromaDB for persistent vector storage
- ✅ **Document retrieval works end-to-end**: Full pipeline from PDF upload to query response
- ✅ **QA responses based on real document embeddings**: Semantic search using sentence-transformers
- ✅ **No hardcoded document sources**: Fallback messages only, no static documentation
- ✅ **PDF upload → question → answer workflow**: Tested and verified
- ✅ **Proper error handling**: Clear messages for missing documents and system errors
- ✅ **Complete documentation**: This guide plus ADVANCED_RAG_FEATURES.md

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                       RAG Integration                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐    ┌──────────────┐ │
│  │   Frontend   │────▶│   FastAPI    │───▶│   Agent      │ │
│  │   (React)    │     │   Backend    │    │   Router     │ │
│  └──────────────┘     └──────────────┘    └──────────────┘ │
│         │                     │                    │         │
│         │ Upload PDF          │ Ingest             │ Query   │
│         ▼                     ▼                    ▼         │
│  ┌──────────────┐     ┌──────────────┐    ┌──────────────┐ │
│  │ File Upload  │     │  PDF Parser  │    │  RAG Tool    │ │
│  │  Component   │     │  (PyPDF2)    │    │              │ │
│  └──────────────┘     └──────────────┘    └──────────────┘ │
│                              │                    │         │
│                              ▼                    │         │
│                       ┌──────────────┐           │         │
│                       │Text Chunking │           │         │
│                       │ (900 chars)  │           │         │
│                       └──────────────┘           │         │
│                              │                    │         │
│                              ▼                    ▼         │
│                       ┌──────────────┐    ┌──────────────┐ │
│                       │  Embeddings  │    │Vector Query  │ │
│                       │(MiniLM-L6-v2)│    │              │ │
│                       └──────────────┘    └──────────────┘ │
│                              │                    │         │
│                              ▼                    │         │
│                       ┌─────────────────────────┐│         │
│                       │   ChromaDB Storage      ││         │
│                       │  (Persistent Vector DB) ◀┘         │
│                       └─────────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Document Ingestion**
   ```
   PDF Upload → Text Extraction → Chunking → Embedding → Vector Storage
   ```

2. **Query Processing**
   ```
   User Query → Query Enhancement → Vector Search → Ranking → Citation Formatting
   ```

3. **Response Generation**
   ```
   Retrieved Chunks → LLM Processing → Formatted Response with Citations
   ```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `chromadb` - Vector database
- `sentence-transformers` - Embedding generation
- `pypdf` - PDF text extraction
- `fastapi` - API backend
- `google-genai` - LLM integration

### 2. Start the Backend

```bash
cd /path/to/agentkit
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Upload a Document

**Via API:**
```bash
curl -X POST "http://localhost:8000/docs/ingest" \
  -F "file=@your_document.pdf" \
  -F "namespace=default" \
  -F "session_id=my_session"
```

**Response:**
```json
{
  "status": "success",
  "message": "Document ingested successfully",
  "chunks": 15,
  "namespace": "default",
  "filename": "your_document.pdf",
  "doc_id": "uuid-generated-id"
}
```

### 4. Query the Document

```bash
curl -X POST "http://localhost:8000/chat" \
  -F "message=What is the main topic of the document?" \
  -F "model=gemini-2.0-flash-001" \
  -F "namespace=default" \
  -F "search_mode=documents" \
  -F "history=[]"
```

**Response includes:**
- `answer` - LLM-generated response
- `tool_output` - Retrieved chunks with citations
- `tool_used` - Tool selected (rag, web, hybrid)
- `execution_time` - Processing time

## Usage Examples

### Example 1: Basic Document Query

```python
# Upload document
response = requests.post(
    "http://localhost:8000/docs/ingest",
    files={"file": open("manual.pdf", "rb")},
    data={"namespace": "technical", "session_id": "user123"}
)

# Query document
response = requests.post(
    "http://localhost:8000/chat",
    data={
        "message": "What are the installation steps?",
        "model": "gemini-2.0-flash-001",
        "namespace": "technical",
        "search_mode": "documents",
        "history": "[]"
    }
)

# Response includes citations
result = response.json()
print(result["tool_output"])  # Shows sources with relevance scores
```

### Example 2: Hybrid Search

```python
# Combine document knowledge with current web information
response = requests.post(
    "http://localhost:8000/chat",
    data={
        "message": "Latest Python features vs our coding standards",
        "model": "gemini-2.0-flash-001",
        "namespace": "company_docs",
        "search_mode": "hybrid",  # Uses both web and documents
        "history": "[]"
    }
)
```

### Example 3: Direct RAG Tool Usage

```python
from agent.tools import _retrieve_context

# Query specific namespace
result = await _retrieve_context(
    query="authentication process",
    namespace="security_docs",
    k=5  # Return top 5 chunks
)

# Result includes formatted citations
print(result)
```

## Testing

### Run All Tests

```bash
# Run comprehensive end-to-end tests
python test_rag_end_to_end.py

# Run advanced RAG feature tests
python test_advanced_rag.py

# Run all tests
./run_tests.sh
```

### Manual Testing Workflow

```bash
# 1. Start backend
uvicorn app.main:app --reload --port 8000

# 2. Create test PDF (in another terminal)
echo "Test document content about AgentKit RAG system" > test.txt
# Convert to PDF or use existing PDF

# 3. Upload document
curl -X POST "http://localhost:8000/docs/ingest" \
  -F "file=@test.pdf" \
  -F "namespace=test"

# 4. Query document
curl -X POST "http://localhost:8000/chat" \
  -F "message=What does the document say?" \
  -F "model=gemini-2.0-flash-001" \
  -F "namespace=test" \
  -F "search_mode=documents" \
  -F "history=[]"

# 5. Verify response includes citations
```

## Configuration

### Vector Store Settings

**Storage Location:**
- Path: `uploads/chroma/`
- Type: Persistent ChromaDB
- Auto-created on first use

**Embedding Model:**
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimensions: 384
- Speed: ~50ms per query
- Download: Automatic on first use

### Document Processing

**Chunking Parameters:**
```python
# In rag/ingest.py
chunk_size = 900      # Characters per chunk
overlap = 150         # Character overlap between chunks
```

**Query Parameters:**
```python
# In agent/tools.py
k = 5                 # Number of chunks to retrieve
namespace = "default" # Namespace for document isolation
```

### API Configuration

**Endpoints:**
- `POST /docs/ingest` - Upload and process documents
- `POST /chat` - Query with RAG support
- `GET /models` - List available models

**File Limits:**
```python
MAX_FILE_SIZE = 10485760  # 10MB
```

## Error Handling

### No Documents Found

**Scenario:** Query returns no results

**Response:**
```
[RAG] No relevant documents found in namespace 'namespace' for query: 'query'

This could mean:
1. No documents have been ingested yet
2. The documents don't contain relevant information
3. Try a different search term or upload relevant documents first
```

**Solution:**
- Upload relevant documents first
- Check namespace is correct
- Try broader search terms

### RAG System Unavailable

**Scenario:** Dependencies not installed

**Response:**
```
[RAG System Unavailable]

The document retrieval system (RAG) is currently not available.
Install dependencies: pip install chromadb sentence-transformers
```

**Solution:**
```bash
pip install chromadb sentence-transformers
```

### Document Processing Error

**Scenario:** PDF processing fails

**Possible Causes:**
- Corrupted PDF
- Password-protected PDF
- File too large

**Solution:**
- Verify PDF is valid
- Check file size < 10MB
- Ensure PDF is not encrypted

## Performance Optimization

### Query Performance

**Typical Response Times:**
- Vector search: 0.1-0.5 seconds
- Query enhancement: <0.01 seconds (LLM)
- Total (RAG only): 0.1-0.6 seconds
- Total (Hybrid): 1-3 seconds (web + documents)

**Optimization Tips:**
1. Reduce `k` parameter for faster queries
2. Use namespace isolation to reduce search space
3. Pre-warm embeddings model on startup
4. Consider caching frequent queries

### Storage Optimization

**Disk Usage:**
- ChromaDB index: ~1MB per 1000 chunks
- Embeddings: 384 floats × 4 bytes × chunks
- Example: 10,000 chunks ≈ 25MB storage

**Optimization Tips:**
1. Regular cleanup of old namespaces
2. Limit document history per user
3. Compress old documents
4. Archive unused namespaces

## Production Deployment

### Checklist

- [ ] Set up persistent ChromaDB storage
- [ ] Configure file upload limits
- [ ] Implement user authentication
- [ ] Add namespace access controls
- [ ] Monitor vector store size
- [ ] Set up backup for ChromaDB data
- [ ] Configure CORS for frontend
- [ ] Add rate limiting
- [ ] Set up logging and monitoring
- [ ] Test error recovery

### Security Considerations

1. **Namespace Isolation:** Ensure users can only access their namespaces
2. **File Validation:** Verify uploaded files are valid PDFs
3. **Size Limits:** Enforce maximum file sizes
4. **Input Sanitization:** Clean user queries before processing
5. **API Authentication:** Require authentication for sensitive operations

### Monitoring

**Key Metrics:**
- Document ingestion rate
- Query response time
- Vector store size
- Error rates
- User activity per namespace

**Logging:**
```python
# Already included in the system
print(f"RAG search error: {e}")
print(f"Query error: {e}")
```

## Troubleshooting

### Common Issues

**1. "ChromaDB import error"**
```bash
pip install --upgrade chromadb
```

**2. "Sentence transformers model not found"**
```bash
# Model downloads automatically on first use
# Ensure internet connection for initial download
```

**3. "No results for uploaded document"**
- Verify document was successfully ingested (check response)
- Confirm namespace matches between upload and query
- Check document contains searchable text (not just images)

**4. "Low relevance scores"**
- Query may not match document content
- Try more specific search terms
- Consider query enhancement is working (requires LLM)

### Debug Mode

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check RAG availability
from agent.tools import RAG_AVAILABLE, vector_query
print(f"RAG Available: {RAG_AVAILABLE}")
print(f"Vector Query: {vector_query}")
```

## Advanced Features

### Namespace Management

```python
from rag.store import list_collections, delete_namespace

# List all namespaces
namespaces = list_collections()
print(f"Available namespaces: {namespaces}")

# Delete a namespace
delete_namespace("old_namespace")
```

### Document Deletion

```python
from rag.store import delete_document

# Delete specific document by ID
delete_document(namespace="default", doc_id="doc-uuid")
```

### Custom Chunking

```python
from rag.ingest import chunk_text

# Custom chunk parameters
chunks = chunk_text(text, chunk_size=500, overlap=100)
```

### Query Enhancement

```python
from agent.tools import _enhance_query

# Enhance query for better semantic matching
enhanced = await _enhance_query("Could you tell me about Python?")
# Result: "Python" (filler words removed)
```

## Related Documentation

- [ADVANCED_RAG_FEATURES.md](ADVANCED_RAG_FEATURES.md) - Detailed feature documentation
- [DOCUMENT_MANAGEMENT.md](DOCUMENT_MANAGEMENT.md) - Document management API
- [NAMESPACE_MANAGEMENT.md](NAMESPACE_MANAGEMENT.md) - Namespace isolation guide
- [README.md](README.md) - General AgentKit documentation

## Support

For issues or questions:
1. Check this documentation
2. Review test files for usage examples
3. Check server logs for errors
4. Open a GitHub issue with details

## Version Information

- RAG System Version: 1.0
- ChromaDB: Compatible with 0.4.x+
- Sentence Transformers: all-MiniLM-L6-v2
- Last Updated: 2025-10-09
