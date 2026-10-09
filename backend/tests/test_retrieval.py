"""
Tests for MultiQueryRetriever, query expansion parser, and document deduplication (Phase 5).
"""

import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

from app.exceptions import VectorStoreNotInitializedError
from app.retrieval import LineListOutputParser, PolicyRetriever


def test_line_list_output_parser():
    parser = LineListOutputParser()
    raw_text = """1. What is the attendance policy?
2) How are attendance marks calculated?
- What are the minimum required attendance hours?
* Can attendance be relaxed for medical reasons?"""

    result = parser.parse(raw_text)
    assert len(result) == 4
    assert result[0] == "What is the attendance policy?"
    assert result[1] == "How are attendance marks calculated?"
    assert result[2] == "What are the minimum required attendance hours?"
    assert result[3] == "Can attendance be relaxed for medical reasons?"


def test_retriever_uninitialized_raises():
    mock_vec_mgr = MagicMock()
    mock_vec_mgr.is_initialized.return_value = False

    retriever = PolicyRetriever(vector_mgr=mock_vec_mgr)
    with pytest.raises(VectorStoreNotInitializedError):
        retriever.retrieve_documents("test question")


def test_retrieval_deduplication():
    mock_vec_mgr = MagicMock()
    mock_vec_mgr.is_initialized.return_value = True

    # Shared document returned by multiple subqueries
    doc1 = Document(page_content="Policy chunk 1", metadata={"chunk_id": "c1", "page_number": 3})
    doc2 = Document(page_content="Policy chunk 2", metadata={"chunk_id": "c2", "page_number": 4})

    mock_vec_store = MagicMock()
    # First query returns doc1 and doc2; second query returns doc1 again
    mock_vec_store.similarity_search_with_score.side_effect = [
        [(doc1, 0.1), (doc2, 0.3)],
        [(doc1, 0.15)],
    ]
    mock_vec_mgr.get_vector_store.return_value = mock_vec_store

    retriever = PolicyRetriever(vector_mgr=mock_vec_mgr)
    # Mock LLM to return 1 expanded subquery
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "1. Alternative question"
    retriever.get_query_expansion_llm = MagicMock(return_value=mock_llm)

    docs, sub_queries = retriever.retrieve_documents("original question")
    assert len(docs) == 2, "Duplicate chunk c1 should be deduplicated"
    assert {d.metadata["chunk_id"] for d in docs} == {"c1", "c2"}
    assert len(sub_queries) == 2
