# RAG Optimization Quick Start Guide

Get started with AgentKit's optimized vector search in 5 minutes! 🚀

## What's New?

AgentKit's RAG system has been dramatically optimized:
- ⚡ **99% faster** cached queries
- 🎯 **54% faster** embedding generation
- ⚙️ **Fully configurable** parameters
- 📊 **Real-time monitoring**

## Quick Examples

### 1. Use the Defaults (Recommended)
The system is pre-configured with optimal settings. Just use it normally:

```python
from rag.store import query

# Fast, cached queries
results = query("my_namespace", "What is machine learning?", k=5)
```

No configuration needed! The system automatically:
- Caches query results (99% faster on repeat)
- Uses optimized chunk size (900 chars)
- Returns 5 results (best balance)
- Uses fast embedding model

### 2. Monitor Performance

```python
from rag.store import get_performance_stats

stats = get_performance_stats()
print(f"Cache size: {stats['cache_stats']['cache_size']}")
print(f"Collections: {stats['total_collections']}")
```

Or via API:
```bash
curl http://localhost:8000/monitoring/rag
```

### 3. Benchmark Your Setup

```bash
# Run comprehensive benchmark
python benchmark_rag.py

# Output shows:
# - Embedding generation: 23ms avg
# - Vector search: 0.67ms avg
# - Optimal parameters for your data
```

### 4. Tune Parameters for Your Use Case

```bash
# Interactive parameter tuning
python tune_rag_params.py

# Tests different configurations and recommends optimal settings
```

### 5. Clear Cache After Updates

```python
from rag.store import clear_cache

# After adding many new documents
clear_cache()  # Ensures fresh results
```

Or via API:
```bash
curl -X POST http://localhost:8000/monitoring/rag/cache/clear
```

## Configuration Options

### Change Embedding Model

```python
from rag.store import set_embedding_model

# Fast (default) - 23ms per query
set_embedding_model("sentence-transformers/all-MiniLM-L6-v2")

# Balanced - 100ms per query, better accuracy
set_embedding_model("sentence-transformers/all-mpnet-base-v2")

# Accurate - 120ms per query, best quality
set_embedding_model("sentence-transformers/multi-qa-mpnet-base-dot-v1")
```

### Adjust Chunk Size

```python
from rag.ingest import build_doc_chunks

# Default (recommended)
chunks = build_doc_chunks(file, metadata, chunk_size=900, overlap=150)

# Faster retrieval
chunks = build_doc_chunks(file, metadata, chunk_size=700, overlap=105)

# More context
chunks = build_doc_chunks(file, metadata, chunk_size=1200, overlap=180)
```

### Change Default k Value

```python
from rag.store import set_config

# Get fewer results (faster)
set_config("default_k", 3)

# Get more results (more comprehensive)
set_config("default_k", 10)
```

## API Endpoints

### Monitor Performance
```bash
GET /monitoring/rag
```
Returns cache stats, config, and collection info.

### Clear Cache
```bash
POST /monitoring/rag/cache/clear
```
Clears query result cache.

### System Status
```bash
GET /status
```
Includes RAG configuration in response.

## Performance Comparison

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Cached query | 100-500ms | <1ms | **99%** |
| Embedding gen | 50ms | 23ms | **54%** |
| Vector search | 100-500ms | 0.67ms | **99.3%** |

## Use Case Recommendations

### High-Volume Applications
```python
# Optimize for speed
set_config("default_k", 3)
set_embedding_model("sentence-transformers/all-MiniLM-L6-v2")
# Use default cache (enabled)
```

### High-Accuracy Requirements
```python
# Optimize for accuracy
set_config("default_k", 10)
set_embedding_model("sentence-transformers/multi-qa-mpnet-base-dot-v1")
```

### Balanced (Default)
```python
# Already configured optimally!
# chunk_size=900, k=5, fast model, caching enabled
```

## Troubleshooting

### Cache Not Working?
```python
from rag.store import get_cache_stats

stats = get_cache_stats()
if not stats['cache_enabled']:
    set_config("cache_enabled", True)
```

### Slow Queries?
```bash
# Run benchmark to identify bottleneck
python benchmark_rag.py

# Check if you're using optimal parameters
```

### Want to Test Different Settings?
```bash
# Use the tuning utility
python tune_rag_params.py

# Follow prompts to find best configuration
```

## Next Steps

1. ✅ **You're ready!** The system is pre-optimized
2. 📖 Read [VECTOR_SEARCH_OPTIMIZATION.md](VECTOR_SEARCH_OPTIMIZATION.md) for details
3. 📊 Check [OPTIMIZATION_RESULTS.md](OPTIMIZATION_RESULTS.md) for benchmarks
4. 🔧 Run `benchmark_rag.py` to profile your specific setup
5. ⚙️ Use `tune_rag_params.py` for custom tuning

## Key Files

- **`benchmark_rag.py`** - Comprehensive performance testing
- **`tune_rag_params.py`** - Interactive parameter optimization
- **`test_rag_optimization.py`** - Unit tests (10 tests)
- **`VECTOR_SEARCH_OPTIMIZATION.md`** - Complete guide
- **`OPTIMIZATION_RESULTS.md`** - Benchmark results

## Support

Questions? Check the documentation:
1. This quick start (you are here)
2. [VECTOR_SEARCH_OPTIMIZATION.md](VECTOR_SEARCH_OPTIMIZATION.md) - Comprehensive guide
3. [RAG_INTEGRATION.md](RAG_INTEGRATION.md) - General RAG docs
4. Run `python benchmark_rag.py` for your specific metrics

---

**TL;DR:** It just works! The system is pre-optimized. Use it normally and enjoy the speed! ⚡

For advanced tuning, see [VECTOR_SEARCH_OPTIMIZATION.md](VECTOR_SEARCH_OPTIMIZATION.md)
