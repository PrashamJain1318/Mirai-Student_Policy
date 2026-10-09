"""
Unit and integration tests for ChromaDB Vector Store Manager (Phase 4).
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document
from app.exceptions import (
    EmbeddingAPIError,
    VectorStoreError,
    VectorStoreNotInitializedError,
)
from app.vector_store import PolicyVectorStoreManager


@pytest.fixture
def temp_chroma_dir(tmp_path):
    chroma_dir = tmp_path / "test_chroma"
    yield chroma_dir
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir, ignore_errors=True)


class FakeEmbeddings:
    """Mock embeddings for testing vector operations without hitting Google API quotas."""
    def embed_documents(self, texts):
        return [[0.1 * (i % 5) for i in range(16)] for _ in texts]

    def embed_query(self, text):
        return [0.1 * (i % 5) for i in range(16)]


def test_missing_api_key_raises(temp_chroma_dir, monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    manager = PolicyVectorStoreManager(
        persist_directory=temp_chroma_dir,
        api_key=None,
    )
    with pytest.raises(EmbeddingAPIError, match="Google API key is missing"):
        manager.get_embeddings()


def test_vector_store_not_initialized(temp_chroma_dir):
    manager = PolicyVectorStoreManager(
        persist_directory=temp_chroma_dir,
        collection_name="empty_collection",
    )
    assert not manager.is_initialized()
    with pytest.raises(VectorStoreNotInitializedError, match="not initialized"):
        manager.similarity_search_with_score("test query")


def test_ingest_and_deduplicate(temp_chroma_dir):
    fake_emb = FakeEmbeddings()
    manager = PolicyVectorStoreManager(
        persist_directory=temp_chroma_dir,
        collection_name="test_dedup_collection",
    )
    # Inject fake embeddings
    manager._embeddings = fake_emb

    sample_docs = [
        Document(
            page_content="Students must maintain 75% attendance.",
            metadata={"chunk_id": "mirai_p005_c001", "source": "handbook.pdf", "page_number": 5},
        ),
        Document(
            page_content="Medical leave permits 65% attendance relaxation.",
            metadata={"chunk_id": "mirai_p005_c002", "source": "handbook.pdf", "page_number": 5},
        ),
    ]

    # First ingestion
    res1 = manager.ingest_documents(
        documents=sample_docs,
        doc_hash="abc123hash",
        handbook_version="2026",
    )
    assert res1["status"] == "success"
    assert res1["added_chunks"] == 2
    assert res1["skipped_duplicates"] == 0
    assert manager.is_initialized()

    # Second ingestion with same documents (testing duplicate rejection)
    res2 = manager.ingest_documents(
        documents=sample_docs,
        doc_hash="abc123hash",
        handbook_version="2026",
    )
    assert res2["status"] == "success"
    assert res2["added_chunks"] == 0
    assert res2["skipped_duplicates"] == 2
    assert res2["total_collection_count"] == 2

    # Similarity search
    results = manager.similarity_search_with_score("attendance policy", k=2)
    assert len(results) == 2
    matched_doc, score = results[0]
    assert "attendance" in matched_doc.page_content.lower()
    assert matched_doc.metadata["page_number"] == 5
