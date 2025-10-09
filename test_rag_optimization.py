"""
Tests for RAG optimization features including:
- Query caching
- Configurable parameters
- Performance monitoring
- Different embedding models
"""

import pytest
from rag.store import (
    query, 
    clear_cache, 
    get_cache_stats, 
    get_config,
    set_config,
    get_performance_stats,
    upsert_chunks,
    set_embedding_model
)
from rag.ingest import chunk_text, build_doc_chunks
import tempfile
import os


def test_query_caching():
    """Test that query results are cached properly."""
    namespace = "cache_test"
    query_text = "test query for caching"
    
    # Setup test data
    test_chunks = [
        {
            "id": "cache_test_1",
            "text": "This is a test document about caching",
            "metadata": {"doc_id": "cache_doc", "filename": "test.txt", "chunk": 0}
        }
    ]
    upsert_chunks(namespace, test_chunks)
    
    # Clear cache first
    clear_cache()
    initial_stats = get_cache_stats()
    initial_size = initial_stats["cache_size"]
    
    # First query - should not be cached
    result1 = query(namespace, query_text, k=5, use_cache=True)
    
    # Check cache grew
    after_first = get_cache_stats()
    assert after_first["cache_size"] > initial_size, "Cache should grow after first query"
    
    # Second query - should be cached
    result2 = query(namespace, query_text, k=5, use_cache=True)
    
    # Results should be identical
    assert result1 == result2, "Cached results should match original"
    
    # Cache size should remain same
    after_second = get_cache_stats()
    assert after_second["cache_size"] == after_first["cache_size"], "Cache should not grow for cached query"
    
    print("✅ Query caching working correctly")


def test_cache_disabled():
    """Test that queries work when cache is disabled."""
    namespace = "cache_disabled_test"
    query_text = "test without cache"
    
    # Setup test data
    test_chunks = [
        {
            "id": "cache_disabled_1",
            "text": "Test document",
            "metadata": {"doc_id": "test_doc", "filename": "test.txt", "chunk": 0}
        }
    ]
    upsert_chunks(namespace, test_chunks)
    
    # Query with cache disabled
    result = query(namespace, query_text, k=5, use_cache=False)
    
    # Should return results
    assert isinstance(result, list), "Should return list of results"
    
    print("✅ Non-cached queries work correctly")


def test_configurable_chunk_sizes():
    """Test that chunk_text accepts different configurations."""
    text = "This is a test. " * 100  # Create longer text
    
    # Test different chunk sizes
    chunks_small = chunk_text(text, chunk_size=500, overlap=75)
    chunks_medium = chunk_text(text, chunk_size=900, overlap=150)
    chunks_large = chunk_text(text, chunk_size=1200, overlap=180)
    
    # Smaller chunks should produce more chunks
    assert len(chunks_small) >= len(chunks_medium), "Smaller chunk size should produce more chunks"
    assert len(chunks_medium) >= len(chunks_large), "Medium chunk size should produce more chunks than large"
    
    # All chunks should be within size limits (approximately)
    for chunk in chunks_small:
        assert len(chunk) <= 600, f"Small chunk too large: {len(chunk)} chars"
    
    for chunk in chunks_medium:
        assert len(chunk) <= 1100, f"Medium chunk too large: {len(chunk)} chars"
    
    print("✅ Configurable chunk sizes working correctly")


def test_build_doc_chunks_with_params():
    """Test that build_doc_chunks accepts chunk size parameters."""
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is test content. " * 100)
        test_file = f.name
    
    try:
        metadata = {"doc_id": "test_doc", "filename": "test.txt"}
        
        # Build chunks with custom parameters
        chunks_small = build_doc_chunks(test_file, metadata, chunk_size=500, overlap=50)
        chunks_large = build_doc_chunks(test_file, metadata, chunk_size=1000, overlap=100)
        
        # Smaller chunks should produce more chunks
        assert len(chunks_small) > len(chunks_large), "Smaller chunk size should produce more chunks"
        
        # Verify metadata preserved
        for chunk in chunks_small:
            assert "id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["doc_id"] == "test_doc"
        
        print("✅ build_doc_chunks with parameters working correctly")
        
    finally:
        os.unlink(test_file)


def test_get_config():
    """Test that configuration can be retrieved."""
    config = get_config()
    
    # Check expected keys exist
    assert "embedding_model" in config
    assert "default_k" in config
    assert "cache_enabled" in config
    
    # Check default values
    assert config["default_k"] == 5
    assert config["cache_enabled"] == True
    
    print("✅ Configuration retrieval working")


def test_set_config():
    """Test that configuration can be updated."""
    original_config = get_config()
    original_k = original_config["default_k"]
    
    # Update config
    new_k = 10
    set_config("default_k", new_k)
    
    # Verify update
    updated_config = get_config()
    assert updated_config["default_k"] == new_k
    
    # Restore original
    set_config("default_k", original_k)
    
    print("✅ Configuration update working")


def test_performance_stats():
    """Test that performance statistics can be retrieved."""
    stats = get_performance_stats()
    
    # Check expected keys
    assert "embedding_model" in stats
    assert "cache_stats" in stats
    assert "config" in stats
    assert "collections" in stats
    
    # Check cache stats structure
    cache_stats = stats["cache_stats"]
    assert "cache_size" in cache_stats
    assert "cache_enabled" in cache_stats
    
    print("✅ Performance stats retrieval working")


def test_cache_clear():
    """Test that cache can be cleared."""
    namespace = "cache_clear_test"
    
    # Add test data
    test_chunks = [
        {
            "id": "clear_test_1",
            "text": "Test document",
            "metadata": {"doc_id": "test", "filename": "test.txt", "chunk": 0}
        }
    ]
    upsert_chunks(namespace, test_chunks)
    
    # Make some queries to populate cache
    query(namespace, "test query 1", k=5)
    query(namespace, "test query 2", k=5)
    
    # Get cache size
    stats_before = get_cache_stats()
    
    # Clear cache
    clear_cache()
    
    # Verify cache is empty
    stats_after = get_cache_stats()
    assert stats_after["cache_size"] == 0, "Cache should be empty after clear"
    
    print("✅ Cache clearing working")


def test_different_k_values():
    """Test queries with different k values."""
    namespace = "k_value_test"
    
    # Setup test data with multiple documents
    test_chunks = [
        {
            "id": f"k_test_{i}",
            "text": f"Test document number {i} with content",
            "metadata": {"doc_id": f"doc_{i}", "filename": f"test_{i}.txt", "chunk": 0}
        }
        for i in range(20)
    ]
    upsert_chunks(namespace, test_chunks)
    
    # Query with different k values
    result_k1 = query(namespace, "test content", k=1, use_cache=False)
    result_k5 = query(namespace, "test content", k=5, use_cache=False)
    result_k10 = query(namespace, "test content", k=10, use_cache=False)
    
    # Verify correct number of results
    assert len(result_k1) <= 1, "k=1 should return at most 1 result"
    assert len(result_k5) <= 5, "k=5 should return at most 5 results"
    assert len(result_k10) <= 10, "k=10 should return at most 10 results"
    
    # More results with higher k
    assert len(result_k1) <= len(result_k5), "Higher k should return more results"
    assert len(result_k5) <= len(result_k10), "Higher k should return more results"
    
    print("✅ Different k values working correctly")


def test_relevance_scoring_optimization():
    """Test that relevance scores are calculated correctly."""
    namespace = "relevance_test"
    
    # Setup test data
    test_chunks = [
        {
            "id": "rel_test_1",
            "text": "Machine learning is a subset of artificial intelligence",
            "metadata": {"doc_id": "doc1", "filename": "ml.txt", "chunk": 0}
        },
        {
            "id": "rel_test_2",
            "text": "Deep learning uses neural networks with multiple layers",
            "metadata": {"doc_id": "doc1", "filename": "ml.txt", "chunk": 1}
        }
    ]
    upsert_chunks(namespace, test_chunks)
    
    # Query
    results = query(namespace, "machine learning", k=5, use_cache=False)
    
    # Check all results have relevance scores
    for result in results:
        assert "relevance_score" in result, "Each result should have relevance score"
        assert 0 <= result["relevance_score"] <= 1, "Relevance score should be between 0 and 1"
        assert "distance" in result, "Each result should have distance"
    
    # Results should be sorted by relevance (lower distance = higher relevance)
    if len(results) > 1:
        for i in range(len(results) - 1):
            # Higher relevance score should come first
            assert results[i]["relevance_score"] >= results[i+1]["relevance_score"], \
                "Results should be sorted by relevance"
    
    print("✅ Relevance scoring optimization working")


if __name__ == "__main__":
    print("Running RAG Optimization Tests\n")
    print("=" * 60)
    
    # Run all tests
    test_query_caching()
    test_cache_disabled()
    test_configurable_chunk_sizes()
    test_build_doc_chunks_with_params()
    test_get_config()
    test_set_config()
    test_performance_stats()
    test_cache_clear()
    test_different_k_values()
    test_relevance_scoring_optimization()
    
    print("\n" + "=" * 60)
    print("✅ All optimization tests passed!")
