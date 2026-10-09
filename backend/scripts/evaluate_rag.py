#!/usr/bin/env python3
"""
CLI Evaluation Script: Runs the four certification questions through the real RAG pipeline
and performs LLM-as-a-judge scoring, exporting results to rag_eval_scores.csv.
Usage:
  python scripts/evaluate_rag.py
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.vector_store import vector_store_manager
from app.evaluation import RAGEvaluator, CERTIFICATION_TEST_CASES


def main():
    print("=" * 75)
    print(" 🏆 MIRAI STUDENT POLICY ADVISOR — RAG CERTIFICATION EVALUATION")
    print("=" * 75)
    print(f"Chat/Judge Model: {settings.GOOGLE_CHAT_MODEL}")
    print(f"Embedding Model: {settings.GOOGLE_EMBEDDING_MODEL}")
    print(f"Chroma Directory: {settings.resolved_chroma_directory}")
    print("-" * 75)

    if not vector_store_manager.is_initialized():
        print("⚠️  WARNING: Vector store is not initialized!")
        print("Please run `python scripts/ingest_handbook.py` first to index the official handbook.")
        print("Attempting to proceed may result in BLOCKED evaluation status.")

    evaluator = RAGEvaluator()
    backend_csv = BACKEND_DIR / "rag_eval_scores.csv"
    root_csv = ROOT_DIR / "rag_eval_scores.csv"

    print("\n⏳ Executing 4 Certification Questions through real RAG pipeline...\n")
    results = evaluator.run_evaluations(output_csv_path=backend_csv)

    # Also copy to root directory for assignment deliverable
    if backend_csv.exists():
        import shutil
        shutil.copyfile(backend_csv, root_csv)

    print("\n" + "=" * 75)
    print(" 📊 EVALUATION SUMMARY RESULTS")
    print("=" * 75)
    for r in results:
        status_icon = "✅" if r["evaluation_status"] == "PASS" else ("❌" if r["evaluation_status"] == "FAIL" else "⚠️")
        print(f"[{r['test_id']}] {status_icon} Status: {r['evaluation_status']} | Score: {r['judge_score']}/5")
        print(f"   Query: {r['question']}")
        print(f"   Answer: {r['generated_answer'][:120]}...")
        print(f"   Reasoning: {r['judge_reasoning']}")
        print("-" * 75)

    print(f"\n📁 Evaluation CSV generated successfully:")
    print(f"   • Backend path: {backend_csv}")
    print(f"   • Root path:    {root_csv}")
    print("=" * 75)


if __name__ == "__main__":
    main()
