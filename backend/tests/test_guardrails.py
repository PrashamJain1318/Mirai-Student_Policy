"""
Tests for Grounding Guardrails, Abstention Detection, and Citation Integrity (Phase 6).
"""

import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

from app.rag_chain import (
    format_context_docs,
    check_abstention,
    PolicyAdvisorChain,
)


def test_format_context_docs_empty():
    assert format_context_docs([]) == "No relevant handbook excerpts retrieved."


def test_format_context_docs_labels():
    docs = [
        Document(
            page_content="Attendance must be 75%.",
            metadata={"source": "Mirai_Handbook.pdf", "page_number": 5},
        ),
        Document(
            page_content="Medical leave allows 65%.",
            metadata={"source": "Mirai_Handbook.pdf", "page_number": 6},
        ),
    ]
    formatted = format_context_docs(docs)
    assert "[Excerpt 1] Document: Mirai_Handbook.pdf | Page: 5" in formatted
    assert "[Excerpt 2] Document: Mirai_Handbook.pdf | Page: 6" in formatted
    assert "Attendance must be 75%." in formatted


def test_check_abstention_triggers():
    # When 0 docs
    assert check_abstention("I found an answer.", num_docs=0) is True

    # Standard abstention phrases
    assert check_abstention("The available handbook excerpts do not establish any monetary fine.", num_docs=2) is True
    assert check_abstention("This is not mentioned in the provided handbook excerpts.", num_docs=2) is True
    assert check_abstention("The handbook does not contain information regarding car parking.", num_docs=2) is True

    # Grounded answer should not trigger abstention
    assert check_abstention("According to Page 5, students with 72% attendance receive 4 marks.", num_docs=2) is False


def test_advisor_chain_empty_retrieval_abstains():
    mock_retriever = MagicMock()
    mock_retriever.retrieve_documents.return_value = ([], ["test question"])

    chain = PolicyAdvisorChain(retriever=mock_retriever)
    res = chain.answer_question("What is the policy on spaceships?")

    assert res.abstained is True
    assert "do not establish" in res.answer.lower()
    assert len(res.sources) == 0


def test_advisor_chain_grounded_answer_with_sources():
    mock_retriever = MagicMock()
    sample_doc = Document(
        page_content="Students with 72% attendance receive 4 marks.",
        metadata={"source": "Mirai_SoT_Policy_Handbook_2026.pdf", "page_number": 5, "chunk_id": "c123"},
    )
    mock_retriever.retrieve_documents.return_value = ([sample_doc], ["attendance marks"])

    chain = PolicyAdvisorChain(retriever=mock_retriever)
    mock_llm_chain = MagicMock()
    mock_llm_chain.invoke.return_value = "Based on Page 5 of the handbook, a student with 72% attendance receives 4 marks."
    chain.build_lcel_chain = MagicMock(return_value=mock_llm_chain)

    res = chain.answer_question("I have 72% attendance. How many marks will I get?")
    assert res.abstained is False
    assert "4 marks" in res.answer
    assert len(res.sources) == 1
    assert res.sources[0]["page"] == 5
    assert res.sources[0]["document"] == "Mirai_SoT_Policy_Handbook_2026.pdf"
