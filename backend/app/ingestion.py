"""
Document ingestion pipeline for MirAI Student Policy Advisor.
Loads official PDF handbooks using PyPDFLoader and applies hierarchical
splitting via RecursiveCharacterTextSplitter (chunk_size=1000, chunk_overlap=200).
"""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

import pypdf
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.exceptions import (
    DocumentValidationError,
    EmptyDocumentError,
    ScannedPDFError,
)
from app.utils import compute_file_hash, generate_chunk_id, sanitize_text


MAX_PDF_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit
MIN_EXTRACTABLE_TEXT_LENGTH = 100       # At least 100 chars total to avoid blank/scanned documents


@dataclass
class IngestionStats:
    source_file: str
    handbook_version: str
    total_pages: int
    total_chunks: int
    total_characters: int
    average_chunk_size: float
    doc_hash: str


def validate_pdf_file(file_path: Path, max_size_bytes: int = MAX_PDF_SIZE_BYTES) -> None:
    """
    Validates PDF file existence, header magic bytes, and size.
    Raises DocumentValidationError if invalid.
    """
    if not file_path.exists():
        raise DocumentValidationError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise DocumentValidationError(f"Path is not a regular file: {file_path}")

    size = file_path.stat().st_size
    if size == 0:
        raise EmptyDocumentError(f"PDF file is empty (0 bytes): {file_path.name}")

    if size > max_size_bytes:
        raise DocumentValidationError(
            f"PDF file size ({size / (1024*1024):.1f} MB) exceeds maximum allowed limit ({max_size_bytes / (1024*1024):.1f} MB)"
        )

    # Check magic header bytes (%PDF-)
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            if header != b"%PDF-":
                raise DocumentValidationError(
                    f"Invalid file format: '{file_path.name}' does not start with valid PDF signature (%PDF-)"
                )
    except OSError as e:
        raise DocumentValidationError(f"Could not read PDF header: {e}")


def load_and_chunk_pdf(
    file_path: Path,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    handbook_version: str = "2026",
) -> Tuple[List[Document], IngestionStats]:
    """
    Loads and chunks a PDF handbook according to strict assignment constraints:
    - PyPDFLoader
    - RecursiveCharacterTextSplitter (chunk_size=1000, chunk_overlap=200)
    - Deterministic chunk metadata and IDs
    - 1-indexed page numbers
    """
    validate_pdf_file(file_path)

    effective_chunk_size = chunk_size or settings.CHUNK_SIZE
    effective_chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    # 1. Read document using pypdf to inspect pages and extractability
    try:
        reader = pypdf.PdfReader(str(file_path))
        num_pages = len(reader.pages)
    except Exception as e:
        raise DocumentValidationError(f"Malformed or corrupt PDF file '{file_path.name}': {e}")

    if num_pages == 0:
        raise EmptyDocumentError(f"PDF '{file_path.name}' contains 0 pages.")

    # 2. Load via LangChain PyPDFLoader
    try:
        loader = PyPDFLoader(str(file_path))
        raw_documents = loader.load()
    except Exception as e:
        raise DocumentValidationError(f"Failed to load PDF via PyPDFLoader: {e}")

    if not raw_documents:
        raise EmptyDocumentError(f"No pages could be extracted from '{file_path.name}'.")

    # 3. Check for scanned PDFs or empty text
    total_extracted_text = "".join(doc.page_content for doc in raw_documents).strip()
    if len(total_extracted_text) < MIN_EXTRACTABLE_TEXT_LENGTH:
        raise ScannedPDFError(
            f"PDF '{file_path.name}' appears to be a scanned document or has negligible extractable text "
            f"({len(total_extracted_text)} characters across {num_pages} pages). Text-based RAG requires readable digital text."
        )

    # 4. Clean text and normalize metadata per page
    doc_hash = compute_file_hash(file_path)
    source_filename = file_path.name

    for doc in raw_documents:
        doc.page_content = sanitize_text(doc.page_content)
        raw_page = doc.metadata.get("page", 0)
        # Normalize to 1-indexed page for human-readable student citations
        doc.metadata["page_number"] = raw_page + 1
        doc.metadata["source"] = source_filename
        doc.metadata["doc_hash"] = doc_hash
        doc.metadata["handbook_version"] = handbook_version

    # 5. Configure RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=effective_chunk_size,
        chunk_overlap=effective_chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    split_chunks = text_splitter.split_documents(raw_documents)

    # 6. Assign deterministic chunk IDs and enrich metadata
    page_chunk_counters: dict[int, int] = {}
    total_chars = 0
    final_chunks: List[Document] = []

    for chunk in split_chunks:
        # Strip and ignore whitespace-only slivers
        content = chunk.page_content.strip()
        if not content:
            continue

        chunk.page_content = content
        page_num = chunk.metadata.get("page_number", 1)
        page_chunk_counters[page_num] = page_chunk_counters.get(page_num, 0) + 1
        chunk_idx = page_chunk_counters[page_num]

        chunk_id = generate_chunk_id(
            doc_id=file_path.stem,
            page_number=page_num,
            chunk_index=chunk_idx,
        )

        chunk.metadata["chunk_id"] = chunk_id
        chunk.metadata["chunk_index"] = chunk_idx
        chunk.metadata["chunk_char_length"] = len(content)

        total_chars += len(content)
        final_chunks.append(chunk)

    if not final_chunks:
        raise EmptyDocumentError(f"Splitting resulted in 0 non-empty text chunks for '{source_filename}'.")

    avg_size = total_chars / len(final_chunks)

    stats = IngestionStats(
        source_file=source_filename,
        handbook_version=handbook_version,
        total_pages=num_pages,
        total_chunks=len(final_chunks),
        total_characters=total_chars,
        average_chunk_size=round(avg_size, 2),
        doc_hash=doc_hash,
    )

    return final_chunks, stats


def ingest_pdf_bytes(
    file_bytes: bytes,
    filename: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    handbook_version: str = "2026",
) -> Tuple[List[Document], IngestionStats]:
    """
    Safely processes an in-memory PDF (such as from FastAPI file upload)
    using a secure temporary file with guaranteed cleanup.
    """
    if not file_bytes:
        raise EmptyDocumentError("Uploaded file is empty (0 bytes).")

    # Basic header check before touching disk
    if not file_bytes.startswith(b"%PDF-"):
        raise DocumentValidationError(f"File '{filename}' does not have a valid PDF header.")

    suffix = Path(filename).suffix or ".pdf"
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(file_bytes)
            temp_path = Path(f.name)
            temp_file = temp_path

        chunks, stats = load_and_chunk_pdf(
            file_path=temp_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            handbook_version=handbook_version,
        )

        # Retain the user-provided filename in metadata rather than the temp filename
        stats.source_file = filename
        for chunk in chunks:
            chunk.metadata["source"] = filename

        return chunks, stats

    finally:
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
