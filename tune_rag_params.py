#!/usr/bin/env python3
"""
RAG Parameter Tuning Utility

This tool helps find optimal parameters for your specific use case by:
- Testing different chunk sizes
- Comparing k values
- Evaluating embedding models
- A/B testing configurations
"""

import asyncio
import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import statistics

from rag.store import (
    query, 
    get_model, 
    set_embedding_model, 
    upsert_chunks,
    clear_cache
)
from rag.ingest import chunk_text, build_doc_chunks
from benchmark_rag import RAGBenchmark, BenchmarkResult


@dataclass
class TuningConfig:
    """Configuration for parameter tuning."""
    chunk_size: int
    overlap: int
    k: int
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __str__(self):
        return f"chunk={self.chunk_size}, overlap={self.overlap}, k={self.k}"


@dataclass
class TuningResult:
    """Results from parameter tuning."""
    config: TuningConfig
    avg_search_time_ms: float
    num_chunks_created: int
    chunk_creation_time_ms: float
    total_score: float  # Combined score for ranking
    
    def __str__(self):
        return (
            f"Config: {self.config}\n"
            f"  Search time: {self.avg_search_time_ms:.2f}ms\n"
            f"  Chunks created: {self.num_chunks_created}\n"
            f"  Chunk time: {self.chunk_creation_time_ms:.2f}ms\n"
            f"  Total score: {self.total_score:.2f}"
        )


class RAGParameterTuner:
    """Tune RAG parameters for optimal performance."""
    
    def __init__(self, test_text: str, test_queries: List[str]):
        self.test_text = test_text
        self.test_queries = test_queries
        self.results: List[TuningResult] = []
    
    def tune_chunk_sizes(self, sizes: List[int] = None) -> List[TuningResult]:
        """Test different chunk sizes with proportional overlap."""
        if sizes is None:
            sizes = [500, 700, 900, 1200, 1500]
        
        print(f"\n{'='*80}")
        print("TUNING CHUNK SIZES")
        print(f"{'='*80}\n")
        
        results = []
        
        for size in sizes:
            overlap = int(size * 0.15)  # 15% overlap
            config = TuningConfig(chunk_size=size, overlap=overlap, k=5)
            
            print(f"Testing chunk_size={size}, overlap={overlap}...")
            
            # Create chunks
            import time
            start = time.perf_counter()
            chunks = chunk_text(self.test_text, chunk_size=size, overlap=overlap)
            chunk_time = (time.perf_counter() - start) * 1000
            
            # Create test namespace and ingest
            namespace = f"tune_chunk_{size}"
            chunk_objs = [
                {
                    "id": f"test_{i}",
                    "text": chunk,
                    "metadata": {"doc_id": "test", "filename": "test.txt", "chunk": i}
                }
                for i, chunk in enumerate(chunks)
            ]
            upsert_chunks(namespace, chunk_objs)
            
            # Test search performance
            search_times = []
            for query_text in self.test_queries:
                start = time.perf_counter()
                query(namespace, query_text, k=5, use_cache=False)
                search_times.append((time.perf_counter() - start) * 1000)
            
            avg_search_time = statistics.mean(search_times)
            
            # Calculate score (lower is better)
            # Balance search speed, chunk count, and chunking time
            score = (
                avg_search_time +  # Search time
                (len(chunks) / 10) +  # Penalty for too many chunks
                (chunk_time / 10)  # Penalty for slow chunking
            )
            
            result = TuningResult(
                config=config,
                avg_search_time_ms=avg_search_time,
                num_chunks_created=len(chunks),
                chunk_creation_time_ms=chunk_time,
                total_score=score
            )
            
            results.append(result)
            self.results.append(result)
            
            print(f"  Chunks: {len(chunks)}, Search: {avg_search_time:.2f}ms, Score: {score:.2f}")
        
        # Sort by score (best first)
        results.sort(key=lambda r: r.total_score)
        
        print(f"\n{'='*80}")
        print("CHUNK SIZE RESULTS (best to worst)")
        print(f"{'='*80}\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result}\n")
        
        return results
    
    def tune_k_values(self, k_values: List[int] = None, chunk_size: int = 900) -> List[TuningResult]:
        """Test different k values for retrieval."""
        if k_values is None:
            k_values = [1, 3, 5, 7, 10, 15, 20]
        
        print(f"\n{'='*80}")
        print("TUNING K VALUES")
        print(f"{'='*80}\n")
        
        # Setup test data
        namespace = "tune_k"
        overlap = int(chunk_size * 0.15)
        chunks = chunk_text(self.test_text, chunk_size=chunk_size, overlap=overlap)
        chunk_objs = [
            {
                "id": f"test_{i}",
                "text": chunk,
                "metadata": {"doc_id": "test", "filename": "test.txt", "chunk": i}
            }
            for i, chunk in enumerate(chunks)
        ]
        upsert_chunks(namespace, chunk_objs)
        
        results = []
        
        for k in k_values:
            config = TuningConfig(chunk_size=chunk_size, overlap=overlap, k=k)
            
            print(f"Testing k={k}...")
            
            # Test search performance
            import time
            search_times = []
            for query_text in self.test_queries:
                start = time.perf_counter()
                query(namespace, query_text, k=k, use_cache=False)
                search_times.append((time.perf_counter() - start) * 1000)
            
            avg_search_time = statistics.mean(search_times)
            
            # Score favors lower k with minimal time penalty
            score = avg_search_time + (k * 0.1)  # Small penalty for higher k
            
            result = TuningResult(
                config=config,
                avg_search_time_ms=avg_search_time,
                num_chunks_created=len(chunks),
                chunk_creation_time_ms=0,
                total_score=score
            )
            
            results.append(result)
            self.results.append(result)
            
            print(f"  Search: {avg_search_time:.2f}ms, Score: {score:.2f}")
        
        # Sort by score
        results.sort(key=lambda r: r.total_score)
        
        print(f"\n{'='*80}")
        print("K VALUE RESULTS (best to worst)")
        print(f"{'='*80}\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. k={result.config.k}, Time: {result.avg_search_time_ms:.2f}ms, Score: {result.total_score:.2f}")
        
        return results
    
    def ab_test_configs(self, configs: List[TuningConfig]) -> List[TuningResult]:
        """A/B test different complete configurations."""
        print(f"\n{'='*80}")
        print("A/B TESTING CONFIGURATIONS")
        print(f"{'='*80}\n")
        
        results = []
        
        for idx, config in enumerate(configs, 1):
            print(f"\nTesting Configuration {idx}:")
            print(f"  Chunk size: {config.chunk_size}")
            print(f"  Overlap: {config.overlap}")
            print(f"  k value: {config.k}")
            print(f"  Model: {config.embedding_model}")
            
            # Set embedding model if different
            set_embedding_model(config.embedding_model)
            clear_cache()  # Clear cache to ensure fair comparison
            
            # Create chunks
            import time
            start = time.perf_counter()
            chunks = chunk_text(self.test_text, chunk_size=config.chunk_size, overlap=config.overlap)
            chunk_time = (time.perf_counter() - start) * 1000
            
            # Setup namespace
            namespace = f"ab_test_{idx}"
            chunk_objs = [
                {
                    "id": f"test_{i}",
                    "text": chunk,
                    "metadata": {"doc_id": "test", "filename": "test.txt", "chunk": i}
                }
                for i, chunk in enumerate(chunks)
            ]
            upsert_chunks(namespace, chunk_objs)
            
            # Test search
            search_times = []
            for query_text in self.test_queries:
                start = time.perf_counter()
                query(namespace, query_text, k=config.k, use_cache=False)
                search_times.append((time.perf_counter() - start) * 1000)
            
            avg_search_time = statistics.mean(search_times)
            
            # Comprehensive score
            score = (
                avg_search_time +
                (len(chunks) / 10) +
                (chunk_time / 10)
            )
            
            result = TuningResult(
                config=config,
                avg_search_time_ms=avg_search_time,
                num_chunks_created=len(chunks),
                chunk_creation_time_ms=chunk_time,
                total_score=score
            )
            
            results.append(result)
            self.results.append(result)
            
            print(f"  Results: {avg_search_time:.2f}ms search, {len(chunks)} chunks, score: {score:.2f}")
        
        # Sort and display
        results.sort(key=lambda r: r.total_score)
        
        print(f"\n{'='*80}")
        print("A/B TEST RESULTS (ranked)")
        print(f"{'='*80}\n")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result}")
        
        return results
    
    def export_results(self, filename: str = "tuning_results.json"):
        """Export tuning results to JSON."""
        export_data = {
            "test_text_length": len(self.test_text),
            "num_queries": len(self.test_queries),
            "results": [
                {
                    "config": asdict(r.config),
                    "metrics": {
                        "avg_search_time_ms": r.avg_search_time_ms,
                        "num_chunks_created": r.num_chunks_created,
                        "chunk_creation_time_ms": r.chunk_creation_time_ms,
                        "total_score": r.total_score
                    }
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n✓ Results exported to {filename}")
    
    def get_recommendation(self) -> TuningConfig:
        """Get recommended configuration based on all tests."""
        if not self.results:
            return TuningConfig(chunk_size=900, overlap=150, k=5)
        
        # Find best overall result
        best = min(self.results, key=lambda r: r.total_score)
        return best.config


async def interactive_tuning():
    """Interactive parameter tuning session."""
    print("RAG Parameter Tuning Tool")
    print("=" * 80 + "\n")
    
    # Sample test data
    test_text = """
    Machine learning is a method of data analysis that automates analytical model building.
    It is a branch of artificial intelligence based on the idea that systems can learn from data,
    identify patterns and make decisions with minimal human intervention. Deep learning is a subset
    of machine learning that uses neural networks with multiple layers. These neural networks attempt
    to simulate the behavior of the human brain—allowing it to learn from large amounts of data.
    Natural language processing (NLP) is a branch of artificial intelligence that helps computers
    understand, interpret and manipulate human language. Vector databases are specialized databases
    designed to store and search vectors efficiently. They are crucial for similarity search and
    recommendation systems. Retrieval-augmented generation (RAG) is a technique that combines
    information retrieval with text generation to produce more accurate and relevant responses.
    Semantic search uses machine learning to understand the intent and contextual meaning behind
    search queries, providing more relevant results than traditional keyword-based search.
    """ * 20  # Make it longer for realistic testing
    
    test_queries = [
        "What is machine learning?",
        "How does deep learning work?",
        "Tell me about vector databases",
        "Explain RAG systems",
        "What is semantic search?"
    ]
    
    tuner = RAGParameterTuner(test_text, test_queries)
    
    # Run tuning tests
    print("Starting parameter tuning...\n")
    
    # 1. Tune chunk sizes
    chunk_results = tuner.tune_chunk_sizes([500, 700, 900, 1200])
    best_chunk_config = chunk_results[0].config
    
    # 2. Tune k values
    k_results = tuner.tune_k_values([1, 3, 5, 7, 10], chunk_size=best_chunk_config.chunk_size)
    best_k_config = k_results[0].config
    
    # 3. A/B test final configurations
    ab_configs = [
        TuningConfig(chunk_size=900, overlap=150, k=5),  # Default
        TuningConfig(chunk_size=700, overlap=105, k=3),  # Fast
        TuningConfig(chunk_size=best_chunk_config.chunk_size, overlap=best_chunk_config.overlap, k=best_k_config.k),  # Optimized
    ]
    
    ab_results = tuner.ab_test_configs(ab_configs)
    
    # Final recommendation
    print(f"\n{'='*80}")
    print("FINAL RECOMMENDATION")
    print(f"{'='*80}\n")
    
    recommendation = tuner.get_recommendation()
    print(f"Based on your test data, we recommend:")
    print(f"  Chunk size: {recommendation.chunk_size} characters")
    print(f"  Overlap: {recommendation.overlap} characters ({recommendation.overlap/recommendation.chunk_size*100:.0f}%)")
    print(f"  k value: {recommendation.k} results")
    print(f"  Embedding model: {recommendation.embedding_model}")
    
    # Export results
    tuner.export_results("rag_tuning_results.json")
    
    print("\n" + "="*80)
    print("Tuning complete! Use these parameters in your production configuration.")
    print("="*80)


if __name__ == "__main__":
    print("Starting RAG parameter tuning...\n")
    asyncio.run(interactive_tuning())
