import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
from functools import lru_cache
import hashlib
import json

# Single, simple store for PoC
_client = None
_model = None
_model_name = None

# namespace -> collection
_collections: Dict[str, any] = {}

# Query result cache (LRU cache for frequent queries)
_query_cache: Dict[str, Dict] = {}
_cache_max_size = 100
_cache_enabled = True

# Configuration for optimization
_config = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",  # Fast, balanced model
    "alternative_models": {
        "fast": "sentence-transformers/all-MiniLM-L6-v2",  # 384 dim, ~50ms
        "balanced": "sentence-transformers/all-mpnet-base-v2",  # 768 dim, ~100ms  
        "accurate": "sentence-transformers/multi-qa-mpnet-base-dot-v1"  # 768 dim, best quality
    },
    "default_k": 5,
    "cache_enabled": True,
    "cache_ttl_seconds": 300  # 5 minutes
}


def get_client():
    """Initialize ChromaDB client once."""
    global _client
    if _client is None:
        # Use persistent storage in uploads directory
        persist_directory = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "uploads", "chroma"
        )
        os.makedirs(persist_directory, exist_ok=True)
        _client = chromadb.PersistentClient(path=persist_directory)
    return _client


def get_model(model_name: Optional[str] = None):
    """Initialize sentence transformer model once with configurable model selection."""
    global _model, _model_name
    
    # Use default model from config if not specified
    if model_name is None:
        model_name = _config["embedding_model"]
    
    # Only reload if model changed
    if _model is None or _model_name != model_name:
        print(f"Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
        _model_name = model_name
    
    return _model


def get_collection(namespace: str):
    """Get or create a collection for the given namespace."""
    client = get_client()
    if namespace not in _collections:
        try:
            _collections[namespace] = client.get_collection(name=namespace)
        except Exception:
            _collections[namespace] = client.create_collection(name=namespace)
    return _collections[namespace]


def upsert_chunks(namespace: str, chunks: List[Dict]):
    """Store document chunks in the vector database."""
    if not chunks:
        return

    col = get_collection(namespace)
    model = get_model()

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Generate embeddings
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    # Upsert to ChromaDB
    col.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)


def _get_cache_key(namespace: str, query_text: str, k: int) -> str:
    """Generate cache key for query."""
    key_data = f"{namespace}:{query_text}:{k}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_cached_result(cache_key: str) -> Optional[List[Dict]]:
    """Get cached query result if available and valid."""
    if not _cache_enabled or not _config["cache_enabled"]:
        return None
    
    if cache_key in _query_cache:
        cached = _query_cache[cache_key]
        # Simple cache without TTL check for now (can add timestamp check if needed)
        return cached.get("result")
    
    return None


def _cache_result(cache_key: str, result: List[Dict]):
    """Cache query result with LRU eviction."""
    global _query_cache
    
    if not _cache_enabled or not _config["cache_enabled"]:
        return
    
    # Implement simple LRU by removing oldest if cache is full
    if len(_query_cache) >= _cache_max_size:
        # Remove first (oldest) entry
        oldest_key = next(iter(_query_cache))
        del _query_cache[oldest_key]
    
    _query_cache[cache_key] = {"result": result}


def query(namespace: str, query_text: str, k: int = 5, use_cache: bool = True) -> List[Dict]:
    """Query the vector database for relevant chunks with enhanced semantic search and caching."""
    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(namespace, query_text, k)
        cached_result = _get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
    
    try:
        col = get_collection(namespace)
        model = get_model()

        # Generate query embedding
        q_emb = model.encode([query_text]).tolist()

        # Query ChromaDB
        res = col.query(query_embeddings=q_emb, n_results=k)

        # Format results with relevance scores
        out = []
        if res["ids"] and res["ids"][0]:
            for i in range(len(res["ids"][0])):
                distance = res["distances"][0][i] if "distances" in res else None
                
                # Calculate relevance score (convert distance to similarity)
                # ChromaDB uses L2 distance, so lower is better
                # Convert to 0-1 scale where 1 is most relevant
                relevance_score = 1.0 / (1.0 + distance) if distance is not None else 0.5
                
                out.append(
                    {
                        "id": res["ids"][0][i],
                        "text": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i],
                        "distance": distance,
                        "relevance_score": round(relevance_score, 3),
                    }
                )

        # Cache the result
        if use_cache:
            _cache_result(cache_key, out)

        return out
    except Exception as e:
        print(f"Query error: {e}")
        return []


def delete_document(namespace: str, doc_id: str):
    """Delete all chunks for a specific document by doc_id."""
    try:
        col = get_collection(namespace)
        # Get all chunks with matching doc_id
        all_docs = col.get()
        
        # Find IDs of chunks belonging to this document
        chunk_ids_to_delete = []
        for i, metadata in enumerate(all_docs.get("metadatas", [])):
            if metadata.get("doc_id") == doc_id:
                chunk_ids_to_delete.append(all_docs["ids"][i])
        
        # Delete the chunks
        if chunk_ids_to_delete:
            col.delete(ids=chunk_ids_to_delete)
            return len(chunk_ids_to_delete)
        return 0
    except Exception as e:
        print(f"Delete document error: {e}")
        raise


def delete_namespace(namespace: str):
    """Delete all data for a namespace."""
    try:
        client = get_client()
        client.delete_collection(name=namespace)
        if namespace in _collections:
            del _collections[namespace]
    except Exception as e:
        print(f"Delete namespace error: {e}")


def list_collections() -> List[str]:
    """List all available collections/namespaces."""
    try:
        client = get_client()
        collections = client.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        print(f"List collections error: {e}")
        return []


def set_embedding_model(model_name: str):
    """Set the embedding model to use (requires restart to take effect)."""
    global _config, _model, _model_name
    _config["embedding_model"] = model_name
    # Clear current model to force reload
    _model = None
    _model_name = None
    print(f"Embedding model set to: {model_name}")


def get_config() -> Dict:
    """Get current RAG configuration."""
    return _config.copy()


def set_config(key: str, value):
    """Update configuration parameter."""
    global _config
    if key in _config:
        _config[key] = value
        print(f"Config updated: {key} = {value}")
    else:
        print(f"Warning: Unknown config key: {key}")


def clear_cache():
    """Clear the query result cache."""
    global _query_cache
    cache_size = len(_query_cache)
    _query_cache = {}
    print(f"Cache cleared ({cache_size} entries removed)")


def get_cache_stats() -> Dict:
    """Get cache statistics."""
    return {
        "cache_size": len(_query_cache),
        "cache_max_size": _cache_max_size,
        "cache_enabled": _cache_enabled and _config["cache_enabled"],
        "cache_keys": list(_query_cache.keys())[:10]  # First 10 keys
    }


def get_performance_stats() -> Dict:
    """Get performance statistics for the vector store."""
    stats = {
        "embedding_model": _model_name or _config["embedding_model"],
        "model_dimensions": 384 if "MiniLM" in (_model_name or _config["embedding_model"]) else 768,
        "cache_stats": get_cache_stats(),
        "config": get_config(),
        "collections": list_collections(),
        "total_collections": len(list_collections())
    }
    
    # Add collection stats
    collection_stats = []
    for ns in list_collections():
        try:
            col = get_collection(ns)
            count = col.count()
            collection_stats.append({
                "namespace": ns,
                "document_count": count
            })
        except Exception:
            pass
    
    stats["collection_details"] = collection_stats
    
    return stats
