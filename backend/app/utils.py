"""
General utility functions for text normalization, hashing, and deterministic chunk ID generation.
"""

import hashlib
import re
from pathlib import Path
from typing import Dict, Any


def compute_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of a file for deterministic versioning and cache invalidation."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()[:12]


def compute_bytes_hash(data: bytes) -> str:
    """Computes SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()[:12]


def sanitize_text(text: str) -> str:
    """Normalizes whitespace and removes null characters while preserving paragraph breaks."""
    text = text.replace("\x00", "")
    # Normalize excessive carriage returns
    text = re.sub(r"\r\n", "\n", text)
    # Normalize multiple blank lines to double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_chunk_id(doc_id: str, page_number: int, chunk_index: int) -> str:
    """
    Generates a deterministic chunk identifier.
    Format: {doc_id}_p{page_number:03d}_c{chunk_index:03d}
    Example: mirai2026_p003_c001
    """
    clean_doc = re.sub(r"[^a-zA-Z0-9_-]", "_", doc_id)
    return f"{clean_doc}_p{page_number:03d}_c{chunk_index:03d}"
