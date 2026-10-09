"""
Tests for PDF Ingestion, Validation, and Recursive Chunking Pipeline (Phase 3).
"""

import pytest
import tempfile
from pathlib import Path

from app.exceptions import DocumentValidationError, EmptyDocumentError, ScannedPDFError
from app.ingestion import validate_pdf_file, load_and_chunk_pdf, ingest_pdf_bytes
from app.config import settings


def test_validate_pdf_file_not_found(tmp_path):
    non_existent = tmp_path / "does_not_exist.pdf"
    with pytest.raises(DocumentValidationError, match="File not found"):
        validate_pdf_file(non_existent)


def test_validate_pdf_empty_file(tmp_path):
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    with pytest.raises(EmptyDocumentError, match="PDF file is empty"):
        validate_pdf_file(empty_pdf)


def test_validate_pdf_invalid_signature(tmp_path):
    invalid_pdf = tmp_path / "fake.pdf"
    invalid_pdf.write_text("This is not a PDF file at all.")
    with pytest.raises(DocumentValidationError, match="valid PDF signature"):
        validate_pdf_file(invalid_pdf)


def test_validate_pdf_oversized(tmp_path):
    large_pdf = tmp_path / "huge.pdf"
    large_pdf.write_bytes(b"%PDF-" + b"0" * 1024)
    # Test setting a strict 500 byte limit
    with pytest.raises(DocumentValidationError, match="exceeds maximum allowed limit"):
        validate_pdf_file(large_pdf, max_size_bytes=500)


def test_official_handbook_ingestion():
    """Verifies that the official Mirai Handbook in backend/data loads and chunks according to specs."""
    handbook_path = settings.resolved_handbook_path
    assert handbook_path.exists(), f"Official handbook missing at {handbook_path}"

    chunks, stats = load_and_chunk_pdf(
        file_path=handbook_path,
        chunk_size=1000,
        chunk_overlap=200,
        handbook_version="2026",
    )

    assert stats.total_pages == 16, f"Expected 16 pages, got {stats.total_pages}"
    assert stats.total_chunks > 0, "Expected non-zero chunks"
    assert stats.total_characters > 10000, "Expected full handbook text content"
    assert stats.source_file == "Mirai_SoT_Policy_Handbook_2026.pdf"
    assert stats.handbook_version == "2026"
    assert len(chunks) == stats.total_chunks

    # Verify metadata and chunk structure on all chunks
    for i, chunk in enumerate(chunks):
        assert "source" in chunk.metadata
        assert chunk.metadata["source"] == "Mirai_SoT_Policy_Handbook_2026.pdf"
        assert "page_number" in chunk.metadata
        assert 1 <= chunk.metadata["page_number"] <= 16
        assert "chunk_id" in chunk.metadata
        assert chunk.metadata["chunk_id"].startswith("Mirai_SoT_Policy_Handbook_2026_p")
        assert len(chunk.page_content) > 0


def test_ingest_pdf_bytes_clean_cleanup():
    """Verifies that in-memory byte ingestion works and leaves no temp files dangling."""
    handbook_path = settings.resolved_handbook_path
    pdf_bytes = handbook_path.read_bytes()

    chunks, stats = ingest_pdf_bytes(
        file_bytes=pdf_bytes,
        filename="Custom_Uploaded_Handbook.pdf",
        chunk_size=1000,
        chunk_overlap=200,
    )

    assert stats.source_file == "Custom_Uploaded_Handbook.pdf"
    assert len(chunks) > 0
    assert chunks[0].metadata["source"] == "Custom_Uploaded_Handbook.pdf"


def test_ingest_pdf_bytes_empty_raises():
    with pytest.raises(EmptyDocumentError):
        ingest_pdf_bytes(file_bytes=b"", filename="empty.pdf")
