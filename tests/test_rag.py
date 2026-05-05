import pytest
from unittest.mock import patch
from rag.embedder import _chunk_text, ingest_document
from rag.retriever import retrieve


def test_chunk_text_basic():
    # New chunker splits on uppercase header lines
    text = "SECTION ONE\nbullet one\nbullet two\n\nSECTION TWO\nbullet three\nbullet four"
    chunks = _chunk_text(text)
    assert len(chunks) == 2
    assert "SECTION ONE" in chunks[0]
    assert "SECTION TWO" in chunks[1]


def test_chunk_text_single_section():
    # Text with no headers should return as one chunk
    text = "just some regular text\nwith no headers\nall lowercase"
    chunks = _chunk_text(text)
    assert len(chunks) == 1
    assert isinstance(chunks[0], str)


def test_chunk_text_ignores_short_uppercase_lines():
    # Lines with 2 or fewer chars shouldn't be treated as headers
    text = "REAL HEADER\nbullet one\n\nA\nbullet two"
    chunks = _chunk_text(text)
    assert "REAL HEADER" in chunks[0]


def test_ingest_document_file_not_found():
    with pytest.raises(FileNotFoundError):
        ingest_document("data/cv/nonexistent.txt", "cv")


def test_retrieve_missing_collection_raises():
    with patch("rag.retriever.chroma.get_collection", side_effect=Exception("not found")):
        with pytest.raises(RuntimeError, match="not found"):
            retrieve("test query", "cv")