import pytest
from unittest.mock import patch
from rag.embedder import _chunk_text, ingest_document
from rag.retriever import retrieve


def test_chunk_text_basic():
    text = " ".join(["word"] * 1100)
    chunks = _chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)


def test_chunk_text_overlap():
    text = " ".join([str(i) for i in range(600)])
    chunks = _chunk_text(text, chunk_size=500, overlap=50)
    last_words_chunk1 = chunks[0].split()[-50:]
    first_words_chunk2 = chunks[1].split()[:50]
    assert last_words_chunk1 == first_words_chunk2


def test_ingest_document_file_not_found():
    with pytest.raises(FileNotFoundError):
        ingest_document("data/cv/nonexistent.txt", "cv")


def test_retrieve_missing_collection_raises():
    with patch("rag.retriever.chroma.get_collection", side_effect=Exception("not found")):
        with pytest.raises(RuntimeError, match="not found"):
            retrieve("test query", "cv")