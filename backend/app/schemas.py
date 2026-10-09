"""
Pydantic v2 request and response schemas for FastAPI endpoints.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RootInfoResponse(BaseModel):
    name: str = Field(default="Autonomous MirAI Student Policy Advisor API")
    version: str = Field(default="1.0.0")
    status: str = Field(default="online")
    handbook_version: str = Field(default="2026")


class HealthStatusResponse(BaseModel):
    status: str = Field(..., description="'healthy' or 'degraded'")
    handbook_file_present: bool
    vector_store_initialized: bool
    indexed_chunks_count: int
    api_key_configured: bool
    embedding_model: str
    chat_model: str
    details: Dict[str, Any] = Field(default_factory=dict)


class SourceItem(BaseModel):
    document: str
    page: int
    excerpt: str
    chunk_id: Optional[str] = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000, description="Student policy question")
    session_id: Optional[str] = Field(default=None, description="Optional conversation tracking identifier")


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = Field(default_factory=list)
    sub_queries: List[str] = Field(default_factory=list)
    abstained: bool = False


class IngestResponse(BaseModel):
    status: str
    source_file: str
    handbook_version: str
    total_pages: int
    total_chunks: int
    total_characters: int
    average_chunk_size: float
    doc_hash: str
    total_collection_count: int
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    error_type: str
