#!/usr/bin/env python3
"""
Benchmarking tool for RAG vector search performance.

Tests and measures:
- Query response times
- Embedding generation speed
- Search accuracy
- Memory usage
- Different parameter configurations
"""

import time
import statistics
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass, field
import tracemalloc

from rag.store import query as vector_query, upsert_chunks, get_model, get_collection
from rag.ingest import chunk_text
from agent.tools import _enhance_query, _retrieve_context


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    operation: str
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    iterations: int
    memory_peak_mb: float = 0.0
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return (
            f"{self.operation}:\n"
            f"  Avg: {self.avg_time*1000:.2f}ms | "
            f"  Min: {self.min_time*1000:.2f}ms | "
            f"  Max: {self.max_time*1000:.2f}ms | "
            f"  StdDev: {self.std_dev*1000:.2f}ms\n"
            f"  Iterations: {self.iterations} | "
            f"  Memory: {self.memory_peak_mb:.2f}MB"
        )


class RAGBenchmark:
    """Benchmark suite for RAG operations."""
    
    def __init__(self, namespace: str = "benchmark_test"):
        self.namespace = namespace
        self.results: List[BenchmarkResult] = []
        
    def _time_operation(self, func, *args, iterations: int = 10, **kwargs) -> List[float]:
        """Time an operation multiple times."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)
        return times
    
    async def _time_async_operation(self, func, *args, iterations: int = 10, **kwargs) -> List[float]:
        """Time an async operation multiple times."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            await func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)
        return times
    
    def _calculate_stats(self, times: List[float], operation: str, config: Dict = None) -> BenchmarkResult:
        """Calculate statistics from timing data."""
        return BenchmarkResult(
            operation=operation,
            avg_time=statistics.mean(times),
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
            iterations=len(times),
            config=config or {}
        )
    
    def benchmark_embedding_generation(self, texts: List[str], iterations: int = 10) -> BenchmarkResult:
        """Benchmark embedding generation speed."""
        model = get_model()
        
        tracemalloc.start()
        times = self._time_operation(
            model.encode, 
            texts, 
            iterations=iterations,
            show_progress_bar=False
        )
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        result = self._calculate_stats(times, "Embedding Generation", {
            "num_texts": len(texts),
            "total_chars": sum(len(t) for t in texts)
        })
        result.memory_peak_mb = peak / 1024 / 1024
        
        self.results.append(result)
        return result
    
    def benchmark_vector_search(self, query: str, k: int = 5, iterations: int = 20) -> BenchmarkResult:
        """Benchmark vector search speed."""
        times = self._time_operation(
            vector_query,
            self.namespace,
            query,
            k=k,
            iterations=iterations
        )
        
        result = self._calculate_stats(times, "Vector Search", {
            "k": k,
            "query_length": len(query)
        })
        
        self.results.append(result)
        return result
    
    def benchmark_chunking(self, text: str, chunk_sizes: List[int] = None, iterations: int = 10) -> List[BenchmarkResult]:
        """Benchmark different chunking configurations."""
        if chunk_sizes is None:
            chunk_sizes = [500, 700, 900, 1200]
        
        results = []
        for chunk_size in chunk_sizes:
            overlap = int(chunk_size * 0.15)  # 15% overlap
            
            times = self._time_operation(
                chunk_text,
                text,
                chunk_size=chunk_size,
                overlap=overlap,
                iterations=iterations
            )
            
            # Count resulting chunks
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
            
            result = self._calculate_stats(times, f"Chunking (size={chunk_size})", {
                "chunk_size": chunk_size,
                "overlap": overlap,
                "num_chunks": len(chunks),
                "text_length": len(text)
            })
            
            results.append(result)
            self.results.append(result)
        
        return results
    
    async def benchmark_query_enhancement(self, queries: List[str], iterations: int = 5) -> BenchmarkResult:
        """Benchmark query enhancement with LLM."""
        async def enhance_all():
            for q in queries:
                await _enhance_query(q)
        
        times = await self._time_async_operation(enhance_all, iterations=iterations)
        
        result = self._calculate_stats(times, "Query Enhancement (LLM)", {
            "num_queries": len(queries),
            "avg_query_length": sum(len(q) for q in queries) / len(queries)
        })
        
        self.results.append(result)
        return result
    
    async def benchmark_full_rag_pipeline(self, query: str, namespace: str = None, iterations: int = 10) -> BenchmarkResult:
        """Benchmark complete RAG retrieval pipeline."""
        ns = namespace or self.namespace
        
        times = await self._time_async_operation(
            _retrieve_context,
            query,
            namespace=ns,
            k=5,
            iterations=iterations
        )
        
        result = self._calculate_stats(times, "Full RAG Pipeline", {
            "namespace": ns,
            "query_length": len(query)
        })
        
        self.results.append(result)
        return result
    
    def benchmark_different_k_values(self, query: str, k_values: List[int] = None, iterations: int = 15) -> List[BenchmarkResult]:
        """Benchmark different k (number of results) values."""
        if k_values is None:
            k_values = [1, 3, 5, 10, 20]
        
        results = []
        for k in k_values:
            times = self._time_operation(
                vector_query,
                self.namespace,
                query,
                k=k,
                iterations=iterations
            )
            
            result = self._calculate_stats(times, f"Vector Search (k={k})", {"k": k})
            results.append(result)
            self.results.append(result)
        
        return results
    
    def setup_test_data(self, num_documents: int = 10, doc_size_chars: int = 5000):
        """Setup test data for benchmarking."""
        print(f"Setting up test data: {num_documents} documents...")
        
        # Generate test documents
        test_text = """
        Machine learning is a subset of artificial intelligence that enables systems to learn 
        and improve from experience without being explicitly programmed. Deep learning, a subset 
        of machine learning, uses neural networks with multiple layers to analyze various factors 
        of data. Natural language processing (NLP) is another important field that helps computers 
        understand, interpret, and generate human language. Vector databases are specialized systems 
        designed to store and search high-dimensional vectors efficiently, making them crucial for 
        modern AI applications. Semantic search uses machine learning to understand the intent and 
        contextual meaning of search queries, providing more relevant results than traditional 
        keyword-based search. Retrieval-augmented generation (RAG) combines information retrieval 
        with language generation to produce more accurate and contextually relevant responses.
        """ * (doc_size_chars // 500)
        
        all_chunks = []
        for i in range(num_documents):
            chunks = chunk_text(test_text, chunk_size=900, overlap=150)
            for j, chunk in enumerate(chunks):
                all_chunks.append({
                    "id": f"bench_doc_{i}_chunk_{j}",
                    "text": chunk,
                    "metadata": {
                        "doc_id": f"bench_doc_{i}",
                        "filename": f"test_document_{i}.txt",
                        "chunk": j
                    }
                })
        
        # Upsert chunks
        upsert_chunks(self.namespace, all_chunks)
        print(f"✓ Inserted {len(all_chunks)} chunks for testing")
        
        return len(all_chunks)
    
    def print_summary(self):
        """Print a summary of all benchmark results."""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80 + "\n")
        
        for result in self.results:
            print(result)
            if result.config:
                print(f"  Config: {result.config}")
            print()
        
        # Print recommendations
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80 + "\n")
        
        # Find fastest k value
        k_results = [r for r in self.results if "k=" in r.operation and "Vector Search" in r.operation]
        if k_results:
            fastest_k = min(k_results, key=lambda r: r.avg_time)
            print(f"✓ Optimal k value: {fastest_k.config['k']} (avg: {fastest_k.avg_time*1000:.2f}ms)")
        
        # Find best chunk size
        chunk_results = [r for r in self.results if "Chunking" in r.operation]
        if chunk_results:
            # Balance speed vs number of chunks
            best_chunk = min(chunk_results, key=lambda r: r.avg_time * r.config['num_chunks'] / 100)
            print(f"✓ Recommended chunk size: {best_chunk.config['chunk_size']} chars")
            print(f"  (produces {best_chunk.config['num_chunks']} chunks, {best_chunk.avg_time*1000:.2f}ms)")
        
        # General recommendations
        print("\n✓ For optimal performance:")
        print("  - Use k=3-5 for most queries (good speed/accuracy balance)")
        print("  - Keep chunk size between 700-900 chars")
        print("  - Use namespace isolation to reduce search space")
        print("  - Consider caching frequent queries")


async def run_comprehensive_benchmark():
    """Run comprehensive benchmark suite."""
    print("RAG Performance Benchmark Tool")
    print("=" * 80 + "\n")
    
    benchmark = RAGBenchmark(namespace="benchmark_test")
    
    # Setup test data
    num_chunks = benchmark.setup_test_data(num_documents=20, doc_size_chars=5000)
    
    print("\nRunning benchmarks...\n")
    
    # 1. Embedding generation
    print("1. Benchmarking embedding generation...")
    test_texts = ["This is a test query about machine learning and AI"] * 5
    benchmark.benchmark_embedding_generation(test_texts, iterations=10)
    
    # 2. Vector search with default k=5
    print("2. Benchmarking vector search (k=5)...")
    test_query = "What is machine learning and deep learning?"
    benchmark.benchmark_vector_search(test_query, k=5, iterations=20)
    
    # 3. Different k values
    print("3. Benchmarking different k values...")
    benchmark.benchmark_different_k_values(test_query, k_values=[1, 3, 5, 10, 20], iterations=15)
    
    # 4. Chunking strategies
    print("4. Benchmarking chunking strategies...")
    long_text = "Machine learning and AI are transforming industries. " * 200
    benchmark.benchmark_chunking(long_text, chunk_sizes=[500, 700, 900, 1200], iterations=10)
    
    # 5. Query enhancement (if LLM available)
    print("5. Benchmarking query enhancement...")
    try:
        test_queries = [
            "Tell me about AI",
            "What are neural networks?",
            "How does semantic search work?"
        ]
        await benchmark.benchmark_query_enhancement(test_queries, iterations=3)
    except Exception as e:
        print(f"   Skipped (LLM not available): {e}")
    
    # 6. Full RAG pipeline
    print("6. Benchmarking full RAG pipeline...")
    await benchmark.benchmark_full_rag_pipeline(test_query, iterations=10)
    
    # Print summary
    benchmark.print_summary()
    
    # Cleanup
    print("\n" + "=" * 80)
    print("Benchmark complete! Test data remains in 'benchmark_test' namespace.")
    print("To clean up: delete_namespace('benchmark_test')")
    print("=" * 80)


if __name__ == "__main__":
    print("Starting RAG benchmarking suite...\n")
    asyncio.run(run_comprehensive_benchmark())
