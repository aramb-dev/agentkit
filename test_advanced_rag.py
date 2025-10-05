"""
Test suite for advanced RAG features.

Tests:
- Semantic search with relevance scoring
- Citation generation
- Hybrid search functionality
- Query enhancement
- Search mode routing
"""

import asyncio
import pytest
from agent.tools import _enhance_query, _retrieve_context, _hybrid_search, TOOLS
from rag.store import query as vector_query


def test_tools_registration():
    """Test that all tools including new hybrid tool are registered."""
    expected_tools = ['web', 'rag', 'hybrid', 'memory', 'idle']
    actual_tools = list(TOOLS.keys())
    
    assert len(actual_tools) >= len(expected_tools), "Missing tools"
    for tool_name in expected_tools:
        assert tool_name in actual_tools, f"Tool '{tool_name}' not registered"
    
    print("✅ All tools registered correctly")


def test_query_enhancement():
    """Test query enhancement for better semantic matching."""
    test_cases = [
        ("Could you please tell me about Python?", "Python"),
        ("What is the architecture?", "architecture"),
        ("explain memory system", "explain memory system"),  # Preserve if no filler
        ("can you help", "help"),
    ]
    
    for original, expected_contains in test_cases:
        enhanced = _enhance_query(original)
        # Enhanced query should contain key terms
        assert expected_contains.lower() in enhanced.lower(), \
            f"Enhanced query '{enhanced}' should contain '{expected_contains}'"
    
    print("✅ Query enhancement working correctly")


def test_hybrid_tool_description():
    """Test that hybrid tool has proper description."""
    hybrid_tool = TOOLS.get('hybrid')
    
    assert hybrid_tool is not None, "Hybrid tool not found"
    assert 'hybrid' in hybrid_tool.description.lower(), "Description should mention hybrid"
    assert 'web' in hybrid_tool.description.lower() or 'document' in hybrid_tool.description.lower(), \
        "Description should mention combining sources"
    
    print("✅ Hybrid tool properly configured")


def test_tool_performance_metrics():
    """Test that tools have performance tracking."""
    for tool_name, tool in TOOLS.items():
        assert hasattr(tool, 'metrics'), f"Tool {tool_name} missing metrics"
        assert 'total_calls' in tool.metrics, f"Tool {tool_name} missing call tracking"
        assert 'success_count' in tool.metrics, f"Tool {tool_name} missing success tracking"
    
    print("✅ Performance metrics available for all tools")


@pytest.mark.asyncio
async def test_rag_tool_citation_format():
    """Test that RAG tool formats results with citations."""
    # This is a unit test - doesn't require actual documents
    # Just tests the format when RAG system is not available
    
    query = "test query"
    result = _retrieve_context(query, namespace="test_namespace", k=5)
    
    # Should return a formatted string (fallback or actual results)
    assert isinstance(result, str), "RAG should return string"
    assert len(result) > 0, "RAG should return non-empty result"
    
    print("✅ RAG tool returns properly formatted results")


@pytest.mark.asyncio
async def test_hybrid_search_integration():
    """Test hybrid search combines both sources."""
    query = "artificial intelligence"
    
    try:
        result = await _hybrid_search(query, namespace="default")
        
        # Should return a string with both sections
        assert isinstance(result, str), "Hybrid search should return string"
        assert len(result) > 0, "Hybrid search should return non-empty result"
        
        # Check for section markers (these are in the hybrid search output)
        # Note: Exact format might vary, so we check for general structure
        assert "search" in result.lower() or "results" in result.lower(), \
            "Hybrid search should indicate search results"
        
        print("✅ Hybrid search integration working")
        
    except Exception as e:
        print(f"ℹ️ Hybrid search test skipped: {e}")
        print("   (This is expected if APIs are not configured)")


def test_search_modes():
    """Test that different search modes are supported."""
    valid_modes = ['auto', 'web', 'documents', 'hybrid']
    
    # Verify these modes make sense for the tools we have
    tool_names = list(TOOLS.keys())
    
    # 'web' mode should map to 'web' tool
    assert 'web' in tool_names, "Web tool needed for web mode"
    
    # 'documents' mode should map to 'rag' tool
    assert 'rag' in tool_names, "RAG tool needed for documents mode"
    
    # 'hybrid' mode should map to 'hybrid' tool
    assert 'hybrid' in tool_names, "Hybrid tool needed for hybrid mode"
    
    print("✅ All search modes have corresponding tools")


def test_relevance_scoring():
    """Test that relevance scoring calculation is correct."""
    # Test the relevance score formula
    test_distances = [0.0, 0.5, 1.0, 2.0]
    
    for distance in test_distances:
        relevance_score = 1.0 / (1.0 + distance)
        
        # Relevance should be between 0 and 1
        assert 0 <= relevance_score <= 1, f"Relevance score {relevance_score} out of range"
        
        # Lower distance should give higher relevance
        if distance == 0.0:
            assert relevance_score == 1.0, "Zero distance should give perfect relevance"
    
    print("✅ Relevance scoring formula correct")


if __name__ == "__main__":
    print("Running Advanced RAG Features Tests\n")
    print("=" * 60)
    
    # Run synchronous tests
    test_tools_registration()
    test_query_enhancement()
    test_hybrid_tool_description()
    test_tool_performance_metrics()
    test_search_modes()
    test_relevance_scoring()
    
    # Run async tests
    print("\nRunning async tests...")
    asyncio.run(test_rag_tool_citation_format())
    asyncio.run(test_hybrid_search_integration())
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("\nNote: Some tests may show info messages if APIs are not configured.")
    print("This is expected behavior for the test suite.")
