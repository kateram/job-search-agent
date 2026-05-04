import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer


chroma = chromadb.PersistentClient(path="chroma_db")
model = SentenceTransformer("all-MiniLM-L6-v2")


def _get_or_create_collection(name: str):
    """Get existing ChromaDB collection or create it."""
    return chroma.get_or_create_collection(name=name)


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.
    Overlap ensures context isn't lost at chunk boundaries.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using a local sentence-transformers model."""
    return model.encode(texts).tolist()


def ingest_document(file_path: str, collection_name: str, chunk_size: int = 500, overlap: int = 50) -> int:
    """
    Read a file, chunk it, embed it, and store in ChromaDB.
    Returns number of chunks stored.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    text = path.read_text(encoding="utf-8")
    chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)  # ← pass them through
    embeddings = _embed(chunks)

    collection = _get_or_create_collection(collection_name)

    collection.upsert(
        ids=[f"{path.stem}_{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"source": path.name, "chunk": i} for i in range(len(chunks))],
    )

    return len(chunks)


def ingest_all():
    cv_dir = Path("data/cv")
    letters_dir = Path("data/cover_letters")

    for file in cv_dir.glob("*.txt"):
        count = ingest_document(str(file), "cv_docs", chunk_size=150, overlap=20)
        print(f"Ingested {file.name} — {count} chunks")

    for file in letters_dir.glob("*.txt"):
        count = ingest_document(str(file), "cover_letters", chunk_size=150, overlap=20)
        print(f"Ingested {file.name} — {count} chunks")


if __name__ == "__main__":
    ingest_all()