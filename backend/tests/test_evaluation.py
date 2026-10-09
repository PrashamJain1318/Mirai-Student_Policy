"""
Tests for RAG Evaluation and LLM-as-a-judge scoring logic (Phase 10).
"""

import pytest
import csv
from unittest.mock import MagicMock
from app.evaluation import RAGEvaluator, CERTIFICATION_TEST_CASES, TestCase


def test_certification_test_cases_count():
    assert len(CERTIFICATION_TEST_CASES) == 4
    test_ids = [tc.test_id for tc in CERTIFICATION_TEST_CASES]
    assert test_ids == ["TEST-01", "TEST-02", "TEST-03", "TEST-04"]


def test_judge_parser_pass():
    evaluator = RAGEvaluator()
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = """SCORE: 5
REASONING: The answer accurately cites 4 marks for 72% attendance without hallucinations.
STATUS: PASS"""
    evaluator._judge_llm = mock_llm

    res = evaluator.judge_answer(
        question="I have 72% attendance.",
        context="72% attendance receives 4 marks.",
        answer="You will receive 4 marks.",
        expected_outcome="The student receives 4 marks.",
    )
    assert res["score"] == 5
    assert res["status"] == "PASS"
    assert "accurately cites" in res["reasoning"]


def test_judge_parser_fail_penalize_monetary_fine():
    evaluator = RAGEvaluator()
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = """SCORE: 1
REASONING: The system fabricated a 500 rupee monetary fine which is not in the handbook.
STATUS: FAIL"""
    evaluator._judge_llm = mock_llm

    res = evaluator.judge_answer(
        question="How much is the fine for smoking?",
        context="Tobacco is prohibited and subject to disciplinary action.",
        answer="The fine is Rs 500.",
        expected_outcome="Tobacco is prohibited and subject to Disciplinary Committee action. No monetary fine.",
    )
    assert res["score"] == 1
    assert res["status"] == "FAIL"
