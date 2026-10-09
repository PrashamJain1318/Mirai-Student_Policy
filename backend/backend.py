"""
FastAPI application entry point for Autonomous MirAI Student Policy Advisor.
Serves GET /, GET /health, POST /ingest, and POST /chat.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import (
    DocumentValidationError,
    EmptyDocumentError,
    ScannedPDFError,
    VectorStoreError,
    VectorStoreNotInitializedError,
    EmbeddingAPIError,
    GenerationError,
)
from app.ingestion import load_and_chunk_pdf, ingest_pdf_bytes
from app.vector_store import vector_store_manager
from app.rag_chain import advisor_chain
from app.schemas import (
    RootInfoResponse,
    HealthStatusResponse,
    ChatRequest,
    ChatResponse,
    IngestResponse,
    SourceItem,
)

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mirai.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Autonomous MirAI Student Policy Advisor API...")
    # Verify local handbook existence
    if settings.resolved_handbook_path.exists():
        logger.info(f"Official handbook found at: {settings.resolved_handbook_path}")
    else:
        logger.warning(f"Official handbook NOT found at: {settings.resolved_handbook_path}")
    yield
    logger.info("Shutting down MirAI Student Policy Advisor API...")


app = FastAPI(
    title="Autonomous MirAI Student Policy Advisor",
    description="Full-stack AI RAG API for Mirai School of Technology 2026 Student Handbook.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
allowed_origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "")
allowed_origins = [
    origin.strip()
    for origin in allowed_origins_env.split(",")
    if origin.strip()
] or [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(DocumentValidationError)
async def handle_document_validation_error(request, exc: DocumentValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "DocumentValidationError"},
    )


@app.exception_handler(VectorStoreNotInitializedError)
async def handle_vector_store_not_initialized(request, exc: VectorStoreNotInitializedError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Handbook index is not initialized. Please trigger POST /ingest first.",
            "error_type": "VectorStoreNotInitializedError",
        },
    )


@app.exception_handler(EmbeddingAPIError)
async def handle_embedding_api_error(request, exc: EmbeddingAPIError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "error_type": "EmbeddingAPIError"},
    )


@app.exception_handler(GenerationError)
async def handle_generation_error(request, exc: GenerationError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "error_type": "GenerationError"},
    )


# API Endpoints
@app.get("/", response_model=RootInfoResponse)
async def get_root_info():
    """Returns basic API service metadata."""
    return RootInfoResponse(
        name="Autonomous MirAI Student Policy Advisor API",
        version="1.0.0",
        status="online",
        handbook_version="2026",
    )


@app.get("/health", response_model=HealthStatusResponse)
async def get_health_status():
    """
    Returns API process health and distinguishes it from dependency readiness.
    Does not make unnecessary external paid API calls during health polling.
    """
    handbook_present = settings.resolved_handbook_path.exists()
    api_key_set = bool(settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))

    collection_stats = vector_store_manager.get_collection_stats()
    vector_initialized = collection_stats.get("initialized", False)
    indexed_chunks = collection_stats.get("count", 0)

    # System is healthy if API is responsive, handbook is present, and index is ready
    is_fully_healthy = handbook_present and vector_initialized and api_key_set
    health_label = "healthy" if is_fully_healthy else "degraded"

    return HealthStatusResponse(
        status=health_label,
        handbook_file_present=handbook_present,
        vector_store_initialized=vector_initialized,
        indexed_chunks_count=indexed_chunks,
        api_key_configured=api_key_set,
        embedding_model=settings.GOOGLE_EMBEDDING_MODEL,
        chat_model=settings.GOOGLE_CHAT_MODEL,
        details={
            "handbook_path": str(settings.resolved_handbook_path),
            "collection_name": settings.CHROMA_COLLECTION_NAME,
        },
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_handbook(
    file: Optional[UploadFile] = File(None),
):
    """
    Ingests the official university policy handbook.
    Supports either an uploaded PDF file or loads the official handbook from disk.
    Executes chunking (1000/200), computes embeddings, and persists to ChromaDB.
    """
    try:
        if file is not None:
            # Process uploaded file
            content = await file.read()
            if not content:
                raise EmptyDocumentError(f"Uploaded file '{file.filename}' is empty.")

            chunks, stats = await asyncio.to_thread(
                ingest_pdf_bytes,
                file_bytes=content,
                filename=file.filename or "Uploaded_Handbook.pdf",
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                handbook_version="2026",
            )
        else:
            # Ingest configured official handbook
            handbook_path = settings.resolved_handbook_path
            if not handbook_path.exists():
                raise DocumentValidationError(
                    f"Official handbook not found at {handbook_path}. "
                    "Please ensure Mirai_SoT_Policy_Handbook_2026.pdf is placed in backend/data/."
                )

            chunks, stats = await asyncio.to_thread(
                load_and_chunk_pdf,
                file_path=handbook_path,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                handbook_version="2026",
            )

        # Persist chunks into ChromaDB
        persist_res = await asyncio.to_thread(
            vector_store_manager.ingest_documents,
            documents=chunks,
            doc_hash=stats.doc_hash,
            handbook_version="2026",
            force_replace=False,
        )

        return IngestResponse(
            status="success",
            source_file=stats.source_file,
            handbook_version=stats.handbook_version,
            total_pages=stats.total_pages,
            total_chunks=stats.total_chunks,
            total_characters=stats.total_characters,
            average_chunk_size=stats.average_chunk_size,
            doc_hash=stats.doc_hash,
            total_collection_count=persist_res.get("total_collection_count", stats.total_chunks),
            message=f"Successfully ingested {persist_res.get('added_chunks', stats.total_chunks)} chunks.",
        )

    except (DocumentValidationError, EmptyDocumentError, ScannedPDFError):
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_with_policy_advisor(
    request: ChatRequest,
):
    """
    Answers student questions strictly grounded in the official handbook.
    Uses MultiQueryRetriever, LCEL chain (gemini-3.8-flash @ 0.0), and factual guardrails.
    """
    if not vector_store_manager.is_initialized():
        raise VectorStoreNotInitializedError()

    try:
        policy_answer = await asyncio.to_thread(
            advisor_chain.answer_question,
            question=request.question,
            k=5,
        )

        source_items = [
            SourceItem(
                document=src["document"],
                page=src["page"],
                excerpt=src["excerpt"],
                chunk_id=src.get("chunk_id"),
            )
            for src in policy_answer.sources
        ]

        return ChatResponse(
            answer=policy_answer.answer,
            sources=source_items,
            sub_queries=policy_answer.sub_queries,
            abstained=policy_answer.abstained,
        )

    except VectorStoreNotInitializedError:
        raise
    except Exception as e:
        logger.error(f"Chat generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during answer generation: {str(e)}",
        )
