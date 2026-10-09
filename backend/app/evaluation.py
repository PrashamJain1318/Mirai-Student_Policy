"""
Evaluation module and LLM-as-a-judge implementation for RAG Certification Tests.
Computes factual correctness, faithfulness, completeness, and writes rag_eval_scores.csv.
"""

import csv
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.exceptions import VectorStoreNotInitializedError
from app.rag_chain import advisor_chain, PolicyAnswer

logger = logging.getLogger("mirai.evaluation")


@dataclass
class TestCase:
    __test__ = False
    test_id: str
    category: str
    question: str
    expected_outcome: str


CERTIFICATION_TEST_CASES = [
    TestCase(
        test_id="TEST-01",
        category="PRECISION_VERIFICATION",
        question="I have 72% attendance. How many attendance marks will I get?",
        expected_outcome="The student receives 4 marks according to the attendance evaluation policy.",
    ),
    TestCase(
        test_id="TEST-02",
        category="MULTI_HOP_REASONING",
        question="I study at the Ratnam campus. I got sick and need medical leave. Who do I email and how many days do I have to submit my documents?",
        expected_outcome="Contact Yashaswini Ma'am and submit supporting medical documents within exactly 7 days of illness or treatment.",
    ),
    TestCase(
        test_id="TEST-03",
        category="PROCESS_VERIFICATION",
        question="We want to start a new Cybersecurity society under the Tech Club. Do we ask Management directly?",
        expected_outcome="40% batch support is required, and the proposal must be submitted to the Faculty Coordinator first, not Management directly.",
    ),
    TestCase(
        test_id="TEST-04",
        category="NEGATIVE_CONSTRAINT_TESTING",
        question="How much is the fine for smoking a cigarette on campus?",
        expected_outcome="Tobacco is strictly prohibited and leads to Disciplinary Committee action. The handbook specifies disciplinary action, NOT a monetary fine. Do not fabricate a monetary fine.",
    ),
]


JUDGE_PROMPT_TEMPLATE = """You are an impartial academic evaluator assessing an AI Student Policy Advisor.
You will evaluate the AI's generated answer against the student's question, the retrieved context excerpts, and the official expected outcome.

CRITERIA:
1. Factual Correctness (Score 1-5): Does the answer align precisely with the expected outcome?
2. Faithfulness / Groundedness: Is the answer strictly derived from the retrieved handbook excerpts?
3. Negative Constraint Adherence: In questions regarding smoking or unlisted penalties, did the system avoid inventing a monetary fine? If any monetary fine is fabricated, immediately give a score of 1.
4. Completeness: Are all required details (names, days, percentages, procedures) covered?

[Question]
{question}

[Retrieved Context]
{context}

[AI Generated Answer]
{answer}

[Expected Outcome]
{expected_outcome}

Format your assessment strictly as:
SCORE: <integer 1 to 5>
REASONING: <concise evaluation explanation>
STATUS: <PASS or FAIL (PASS requires score >= 4)>
"""

JUDGE_PROMPT = PromptTemplate(
    input_variables=["question", "context", "answer", "expected_outcome"],
    template=JUDGE_PROMPT_TEMPLATE,
)


class RAGEvaluator:
    """
    Executes benchmark queries and performs LLM-as-a-judge scoring.
    """

    def __init__(self, judge_model_name: Optional[str] = None):
        self.judge_model_name = judge_model_name or settings.GOOGLE_CHAT_MODEL
        self._judge_llm: Optional[ChatGoogleGenerativeAI] = None

    def get_judge_llm(self) -> ChatGoogleGenerativeAI:
        if self._judge_llm is None:
            self._judge_llm = ChatGoogleGenerativeAI(
                model=self.judge_model_name,
                temperature=0.0,
                api_key=settings.GOOGLE_API_KEY,
            )
        return self._judge_llm

    def judge_answer(
        self,
        question: str,
        context: str,
        answer: str,
        expected_outcome: str,
    ) -> Dict[str, Any]:
        """Invokes judge LLM to evaluate the generated answer."""
        llm = self.get_judge_llm()
        formatted = JUDGE_PROMPT.format(
            question=question,
            context=context,
            answer=answer,
            expected_outcome=expected_outcome,
        )

        try:
            res = llm.invoke(formatted)
            raw_content = res.content if hasattr(res, "content") else str(res)
            if isinstance(raw_content, list):
                content = "\n".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in raw_content
                )
            else:
                content = str(raw_content)

            # Parse score, reasoning, status
            score = 3
            reasoning = content
            eval_status = "PASS"

            for line in content.split("\n"):
                line_str = line.strip()
                if line_str.startswith("SCORE:"):
                    try:
                        score = int(line_str.replace("SCORE:", "").strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                elif line_str.startswith("STATUS:"):
                    eval_status = line_str.replace("STATUS:", "").strip()
                elif line_str.startswith("REASONING:"):
                    reasoning = line_str.replace("REASONING:", "").strip()

            if eval_status not in ["PASS", "FAIL"]:
                eval_status = "PASS" if score >= 4 else "FAIL"

            return {
                "score": score,
                "reasoning": reasoning,
                "status": eval_status,
            }
        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}")
            return {
                "score": 0,
                "reasoning": f"Judge API evaluation error: {str(e)}",
                "status": "BLOCKED",
            }

    def run_evaluations(self, output_csv_path: Path) -> List[Dict[str, Any]]:
        """Runs the four certification questions through the active pipeline and writes CSV."""
        results = []
        for tc in CERTIFICATION_TEST_CASES:
            logger.info(f"Evaluating {tc.test_id}: {tc.question}")
            try:
                policy_answer: PolicyAnswer = advisor_chain.answer_question(tc.question, k=5)
                context_str = "\n".join(f"[P.{s['page']}] {s['excerpt']}" for s in policy_answer.sources)
                source_pages_str = ", ".join(str(s["page"]) for s in policy_answer.sources)

                judge_res = self.judge_answer(
                    question=tc.question,
                    context=context_str,
                    answer=policy_answer.answer,
                    expected_outcome=tc.expected_outcome,
                )

                row = {
                    "test_id": tc.test_id,
                    "question": tc.question,
                    "expected_outcome": tc.expected_outcome,
                    "retrieved_context": context_str.replace("\n", " "),
                    "generated_answer": policy_answer.answer.replace("\n", " "),
                    "source_pages": source_pages_str,
                    "judge_score": judge_res["score"],
                    "judge_reasoning": judge_res["reasoning"].replace("\n", " "),
                    "evaluation_status": judge_res["status"],
                }
            except Exception as e:
                row = {
                    "test_id": tc.test_id,
                    "question": tc.question,
                    "expected_outcome": tc.expected_outcome,
                    "retrieved_context": "",
                    "generated_answer": f"Error: {e}",
                    "source_pages": "",
                    "judge_score": 0,
                    "judge_reasoning": f"RAG execution failed: {e}",
                    "evaluation_status": "BLOCKED",
                }
            results.append(row)

        # Write to CSV
        fieldnames = [
            "test_id",
            "question",
            "expected_outcome",
            "retrieved_context",
            "generated_answer",
            "source_pages",
            "judge_score",
            "judge_reasoning",
            "evaluation_status",
        ]
        with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)

        return results
