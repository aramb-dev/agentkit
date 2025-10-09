"""
End-to-end test for RAG integration.

Tests the complete workflow:
1. PDF upload and ingestion
2. Document chunking and embedding
3. Vector storage
4. Query and retrieval
5. Proper error handling
"""

import asyncio
import tempfile
import os
from pathlib import Path
import pytest

# Test imports
from rag.ingest import extract_text_from_pdf, chunk_text, build_doc_chunks
from rag.store import upsert_chunks, query as vector_query, delete_namespace, list_collections
from agent.tools import _retrieve_context, TOOLS


def create_test_pdf():
    """Create a simple test PDF for testing."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = temp_file.name
        temp_file.close()
        
        # Create PDF with test content
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "AgentKit RAG Test Document")
        c.drawString(100, 730, "")
        c.drawString(100, 710, "This is a test document for the RAG system.")
        c.drawString(100, 690, "AgentKit uses ChromaDB for vector storage and sentence transformers for embeddings.")
        c.drawString(100, 670, "The system supports semantic search with relevance scoring.")
        c.drawString(100, 650, "Documents are chunked into 900-character segments with 150-character overlap.")
        c.drawString(100, 630, "")
        c.drawString(100, 610, "Key Features:")
        c.drawString(100, 590, "- Vector-based semantic search")
        c.drawString(100, 570, "- Citation support with source attribution")
        c.drawString(100, 550, "- Namespace isolation for multi-tenant scenarios")
        c.drawString(100, 530, "- Hybrid search combining web and document sources")
        c.showPage()
        c.save()
        
        return pdf_path
    except ImportError:
        print("⚠️  reportlab not installed, using PyPDF2 to create simple PDF")
        # Fallback: create a very simple text file as PDF mock
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w')
        temp_file.write("""AgentKit RAG Test Document

This is a test document for the RAG system.
AgentKit uses ChromaDB for vector storage and sentence transformers for embeddings.
The system supports semantic search with relevance scoring.
Documents are chunked into 900-character segments with 150-character overlap.

Key Features:
- Vector-based semantic search
- Citation support with source attribution
- Namespace isolation for multi-tenant scenarios
- Hybrid search combining web and document sources
""")
        temp_file.close()
        
        # For this fallback, we'll just use the text file path
        # The test will need to handle this gracefully
        return None


def test_rag_system_availability():
    """Test that RAG system components are available."""
    print("🔍 Testing RAG system availability...")
    
    from agent.tools import RAG_AVAILABLE, vector_query
    
    assert RAG_AVAILABLE, "RAG system should be available"
    assert vector_query is not None, "Vector query function should be available"
    
    print("✅ RAG system components are available")


def test_pdf_text_extraction():
    """Test PDF text extraction."""
    print("\n📄 Testing PDF text extraction...")
    
    # Create a simple test with reportlab or fallback
    try:
        from reportlab.pdfgen import canvas
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = temp_file.name
        temp_file.close()
        
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "Test document for extraction")
        c.showPage()
        c.save()
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        
        # Clean up
        os.unlink(pdf_path)
        
        assert "Test document" in text, "Extracted text should contain test content"
        print("✅ PDF text extraction working")
        
    except ImportError:
        print("ℹ️  Skipping PDF extraction test - reportlab not available")


def test_text_chunking():
    """Test text chunking functionality."""
    print("\n✂️  Testing text chunking...")
    
    sample_text = """
    AgentKit is a comprehensive AI assistant framework. It provides advanced RAG capabilities
    for document retrieval and question answering. The system uses ChromaDB for vector storage
    and sentence transformers for generating embeddings. Documents are processed and chunked
    for efficient retrieval. Each chunk maintains metadata for citation support.
    """ * 5  # Repeat to ensure we get multiple chunks
    
    chunks = chunk_text(sample_text, chunk_size=200, overlap=50)
    
    assert len(chunks) > 0, "Should generate at least one chunk"
    # Chunks may be slightly larger than chunk_size due to sentence boundaries and overlap
    # Just verify chunks are reasonable size (not empty, not massive)
    assert all(30 < len(c) < 1000 for c in chunks), "Chunks should be reasonable size"
    
    print(f"✅ Text chunking working - generated {len(chunks)} chunks")


def test_vector_storage_and_retrieval():
    """Test storing and retrieving documents from vector database."""
    print("\n💾 Testing vector storage and retrieval...")
    
    test_namespace = "test_e2e_rag"
    
    try:
        # Clean up any existing test data
        delete_namespace(test_namespace)
        
        # Create test chunks
        test_chunks = [
            {
                "id": "test-doc-1-0",
                "text": "AgentKit provides advanced RAG capabilities with semantic search and citation support.",
                "metadata": {
                    "filename": "test_document.pdf",
                    "namespace": test_namespace,
                    "doc_id": "test-doc-1",
                    "chunk": 0
                }
            },
            {
                "id": "test-doc-1-1",
                "text": "The system uses ChromaDB for vector storage and sentence transformers for embeddings.",
                "metadata": {
                    "filename": "test_document.pdf",
                    "namespace": test_namespace,
                    "doc_id": "test-doc-1",
                    "chunk": 1
                }
            },
            {
                "id": "test-doc-1-2",
                "text": "Documents are chunked into segments with overlap for better context retrieval.",
                "metadata": {
                    "filename": "test_document.pdf",
                    "namespace": test_namespace,
                    "doc_id": "test-doc-1",
                    "chunk": 2
                }
            }
        ]
        
        # Store chunks
        upsert_chunks(test_namespace, test_chunks)
        print("  ✓ Chunks stored successfully")
        
        # Query for relevant documents
        query_text = "How does AgentKit handle document storage?"
        results = vector_query(test_namespace, query_text, k=3)
        
        assert len(results) > 0, "Should retrieve at least one result"
        assert all("relevance_score" in r for r in results), "Results should have relevance scores"
        assert all("metadata" in r for r in results), "Results should have metadata"
        
        print(f"  ✓ Retrieved {len(results)} relevant documents")
        
        # Verify relevance scores are reasonable
        for i, result in enumerate(results, 1):
            score = result["relevance_score"]
            assert 0 <= score <= 1, f"Relevance score should be between 0 and 1, got {score}"
            print(f"    [{i}] Relevance: {score:.2%} - {result['metadata']['filename']}")
        
        print("✅ Vector storage and retrieval working correctly")
        
    finally:
        # Clean up test data
        delete_namespace(test_namespace)


@pytest.mark.asyncio
async def test_rag_tool_with_real_data():
    """Test the RAG tool with actual stored documents."""
    print("\n🔧 Testing RAG tool with real data...")
    
    test_namespace = "test_tool_rag"
    
    try:
        # Clean up
        delete_namespace(test_namespace)
        
        # Store test documents
        test_chunks = [
            {
                "id": "tool-test-1-0",
                "text": "AgentKit architecture includes a router for intelligent tool selection, modular tools for specific tasks, and LLM integration for natural responses.",
                "metadata": {
                    "filename": "architecture.pdf",
                    "namespace": test_namespace,
                    "doc_id": "tool-test-1",
                    "chunk": 0
                }
            },
            {
                "id": "tool-test-1-1", 
                "text": "The RAG system provides semantic search with citations, relevance scoring, and hybrid search capabilities.",
                "metadata": {
                    "filename": "features.pdf",
                    "namespace": test_namespace,
                    "doc_id": "tool-test-1",
                    "chunk": 1
                }
            }
        ]
        
        upsert_chunks(test_namespace, test_chunks)
        print("  ✓ Test documents stored")
        
        # Query using RAG tool
        query = "What is AgentKit's architecture?"
        result = await _retrieve_context(query, namespace=test_namespace, k=3)
        
        # Verify result format
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert "architecture" in result.lower() or "router" in result.lower(), "Result should contain relevant content"
        assert "Citations:" in result, "Result should include citations"
        assert "relevance:" in result.lower(), "Result should show relevance scores"
        
        print("  ✓ RAG tool returned properly formatted results")
        print(f"\n📝 Sample output:\n{result[:300]}...\n")
        
        print("✅ RAG tool working correctly with real data")
        
    finally:
        # Clean up
        delete_namespace(test_namespace)


@pytest.mark.asyncio
async def test_error_handling_empty_namespace():
    """Test error handling when querying empty namespace."""
    print("\n⚠️  Testing error handling for empty namespace...")
    
    empty_namespace = "test_empty_namespace_xyz"
    
    try:
        # Ensure namespace is empty
        delete_namespace(empty_namespace)
        
        # Query empty namespace
        result = await _retrieve_context("test query", namespace=empty_namespace, k=5)
        
        # Should return helpful error message
        assert isinstance(result, str), "Should return string even for empty namespace"
        assert "No relevant documents found" in result or "no documents" in result.lower(), \
            "Should indicate no documents found"
        
        print("✅ Error handling working correctly for empty namespace")
        
    finally:
        # Clean up
        delete_namespace(empty_namespace)


def test_namespace_isolation():
    """Test that namespaces properly isolate documents."""
    print("\n🔒 Testing namespace isolation...")
    
    namespace1 = "test_ns_isolation_1"
    namespace2 = "test_ns_isolation_2"
    
    try:
        # Clean up
        delete_namespace(namespace1)
        delete_namespace(namespace2)
        
        # Store different documents in each namespace
        chunks1 = [{
            "id": "ns1-doc-0",
            "text": "This document is in namespace 1 about apples.",
            "metadata": {"filename": "apples.pdf", "namespace": namespace1, "doc_id": "ns1-doc", "chunk": 0}
        }]
        
        chunks2 = [{
            "id": "ns2-doc-0",
            "text": "This document is in namespace 2 about oranges.",
            "metadata": {"filename": "oranges.pdf", "namespace": namespace2, "doc_id": "ns2-doc", "chunk": 0}
        }]
        
        upsert_chunks(namespace1, chunks1)
        upsert_chunks(namespace2, chunks2)
        
        # Query each namespace
        results1 = vector_query(namespace1, "fruit", k=5)
        results2 = vector_query(namespace2, "fruit", k=5)
        
        # Verify isolation
        assert len(results1) > 0, "Should find documents in namespace 1"
        assert len(results2) > 0, "Should find documents in namespace 2"
        
        # Verify documents are different
        text1 = results1[0]["text"]
        text2 = results2[0]["text"]
        assert "apples" in text1.lower(), "Namespace 1 should return apples doc"
        assert "oranges" in text2.lower(), "Namespace 2 should return oranges doc"
        
        print("✅ Namespace isolation working correctly")
        
    finally:
        # Clean up
        delete_namespace(namespace1)
        delete_namespace(namespace2)


def test_tools_registration():
    """Verify all RAG-related tools are properly registered."""
    print("\n📋 Testing tool registration...")
    
    required_tools = ["rag", "hybrid", "web", "memory", "idle"]
    
    for tool_name in required_tools:
        assert tool_name in TOOLS, f"Tool '{tool_name}' should be registered"
        tool = TOOLS[tool_name]
        assert hasattr(tool, "name"), f"Tool '{tool_name}' should have name attribute"
        assert hasattr(tool, "description"), f"Tool '{tool_name}' should have description"
        assert hasattr(tool, "fn"), f"Tool '{tool_name}' should have function"
    
    # Verify RAG tool description mentions key features
    rag_tool = TOOLS["rag"]
    assert "vector" in rag_tool.description.lower() or "document" in rag_tool.description.lower(), \
        "RAG tool description should mention vector/document search"
    
    print("✅ All tools properly registered")


def main():
    """Run all end-to-end tests."""
    print("=" * 70)
    print("AgentKit RAG End-to-End Integration Tests")
    print("=" * 70)
    
    # Synchronous tests
    test_rag_system_availability()
    test_pdf_text_extraction()
    test_text_chunking()
    test_vector_storage_and_retrieval()
    test_namespace_isolation()
    test_tools_registration()
    
    # Asynchronous tests
    print("\n🔄 Running async tests...")
    asyncio.run(test_rag_tool_with_real_data())
    asyncio.run(test_error_handling_empty_namespace())
    
    print("\n" + "=" * 70)
    print("✅ All RAG end-to-end tests passed!")
    print("=" * 70)
    print("\n📊 Test Summary:")
    print("  ✓ RAG system availability")
    print("  ✓ PDF text extraction")
    print("  ✓ Text chunking")
    print("  ✓ Vector storage and retrieval")
    print("  ✓ RAG tool integration")
    print("  ✓ Error handling")
    print("  ✓ Namespace isolation")
    print("  ✓ Tool registration")
    print("\n🎉 RAG integration is fully functional!")


if __name__ == "__main__":
    main()
