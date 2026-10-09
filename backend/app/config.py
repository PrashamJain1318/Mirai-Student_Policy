"""
Central Configuration module for MirAI Student Policy Advisor Backend.
Uses Pydantic Settings to manage environment variables, RAG hyperparameters,
and model identifiers.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# Base directory for backend (parent directory of app/)
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Google API Key for Gemini and Embeddings
    GOOGLE_API_KEY: Optional[str] = None

    # Model identifiers as mandated by assignment requirements
    GOOGLE_EMBEDDING_MODEL: str = "text-embedding-004"
    GOOGLE_CHAT_MODEL: str = "gemini-3.8-flash"
    TEMPERATURE: float = 0.0

    # Ingestion & Chunking parameters
    HANDBOOK_PATH: str = "./data/Mirai_SoT_Policy_Handbook_2026.pdf"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Persistent Vector Database settings
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "mirai_policy_collection"

    # Server Configuration
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_handbook_path(self) -> Path:
        """Returns the absolute resolved path to the handbook PDF."""
        p = Path(self.HANDBOOK_PATH)
        if not p.is_absolute():
            return (BACKEND_DIR / p).resolve()
        return p.resolve()

    @property
    def resolved_chroma_directory(self) -> Path:
        """Returns the absolute resolved path to the ChromaDB directory."""
        p = Path(self.CHROMA_PERSIST_DIRECTORY)
        if not p.is_absolute():
            return (BACKEND_DIR / p).resolve()
        return p.resolve()


# Singleton settings instance
settings = Settings()
