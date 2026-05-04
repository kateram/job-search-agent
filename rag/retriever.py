import chromadb
from rag.embedder import _embed


chroma = chromadb.PersistentClient(path="chroma_db")



def retrieve(query: str, collection_name: str, n_results: int = 3) -> list[str]:
    """
    Find the most relevant chunks for a query.
    Returns a list of text chunks ranked by similarity.
    collection_name: 'cv' or 'cover_letters'
    """
    try:
        collection = chroma.get_collection(collection_name)
    except Exception:
        raise RuntimeError(
            f"Collection '{collection_name}' not found. "
            f"Run embedder.ingest_all() first."
        )

    embedding = _embed([query])[0]

    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
    )

    return results["documents"][0]