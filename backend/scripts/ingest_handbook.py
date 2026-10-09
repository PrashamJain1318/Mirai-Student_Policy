#!/usr/bin/env python3
"""
CLI script to ingest the official Mirai Policy Handbook into ChromaDB.
Usage:
  python scripts/ingest_handbook.py [--force]
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.ingestion import load_and_chunk_pdf
from app.vector_store import vector_store_manager


def main():
    parser = argparse.ArgumentParser(description="Ingest official Mirai Policy Handbook into persistent ChromaDB.")
    parser.add_argument("--force", action="store_true", help="Force replace existing ChromaDB collection.")
    parser.add_argument("--path", type=str, default=None, help="Custom path to PDF handbook.")
    args = parser.parse_args()

    handbook_path = Path(args.path) if args.path else settings.resolved_handbook_path

    print("=" * 70)
    print(" 📚 AUTONOMOUS MIRAI POLICY HANDBOOK INGESTION")
    print("=" * 70)
    print(f"Target PDF File: {handbook_path}")
    print(f"Chroma Directory: {settings.resolved_chroma_directory}")
    print(f"Collection Name: {settings.CHROMA_COLLECTION_NAME}")
    print(f"Embedding Model: {settings.GOOGLE_EMBEDDING_MODEL}")
    print(f"Chunk Size: {settings.CHUNK_SIZE} | Chunk Overlap: {settings.CHUNK_OVERLAP}")
    print("-" * 70)

    if not handbook_path.exists():
        print(f"❌ ERROR: Handbook not found at {handbook_path}")
        print("Please place Mirai_SoT_Policy_Handbook_2026.pdf into backend/data/")
        sys.exit(1)

    print("⏳ [1/2] Loading and chunking PDF handbook...")
    chunks, stats = load_and_chunk_pdf(
        file_path=handbook_path,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        handbook_version="2026",
    )

    print(f"   • Total Pages: {stats.total_pages}")
    print(f"   • Total Chunks: {stats.total_chunks}")
    print(f"   • Total Characters: {stats.total_characters}")
    print(f"   • Average Chunk Length: {stats.average_chunk_size} chars")
    print(f"   • Document Hash (SHA-256): {stats.doc_hash}")

    print("\n⏳ [2/2] Generating embeddings and persisting to ChromaDB...")
    try:
        persist_res = vector_store_manager.ingest_documents(
            documents=chunks,
            doc_hash=stats.doc_hash,
            handbook_version="2026",
            force_replace=args.force,
        )
        print(f"✅ Ingestion Successful!")
        print(f"   • Added Chunks: {persist_res['added_chunks']}")
        print(f"   • Skipped Duplicates: {persist_res['skipped_duplicates']}")
        print(f"   • Total Vectors in Collection: {persist_res['total_collection_count']}")
    except Exception as e:
        print(f"❌ Vector store error: {e}")
        print("Note: If GOOGLE_API_KEY is not set or quota is exceeded, set GOOGLE_API_KEY in backend/.env")
        sys.exit(1)

    print("=" * 70)


if __name__ == "__main__":
    main()
