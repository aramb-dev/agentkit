import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import os

# Single, simple store for PoC
_client = None
_model = None

# namespace -> collection
_collections: Dict[str, any] = {}


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


def get_model():
    """Initialize sentence transformer model once."""
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
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


def query(namespace: str, query_text: str, k: int = 5) -> List[Dict]:
    """Query the vector database for relevant chunks."""
    try:
        col = get_collection(namespace)
        model = get_model()

        # Generate query embedding
        q_emb = model.encode([query_text]).tolist()

        # Query ChromaDB
        res = col.query(query_embeddings=q_emb, n_results=k)

        # Format results
        out = []
        if res["ids"] and res["ids"][0]:
            for i in range(len(res["ids"][0])):
                out.append(
                    {
                        "id": res["ids"][0][i],
                        "text": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i],
                        "distance": (
                            res["distances"][0][i] if "distances" in res else None
                        ),
                    }
                )

        return out
    except Exception as e:
        print(f"Query error: {e}")
        return []


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
