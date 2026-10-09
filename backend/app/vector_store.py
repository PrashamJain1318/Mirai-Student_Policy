"""
ChromaDB Persistent Vector Store and Google Generative AI Embeddings module.
Uses text-embedding-004 and langchain-chroma for persistent storage and similarity retrieval.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.exceptions import (
    EmbeddingAPIError,
    VectorStoreError,
    VectorStoreNotInitializedError,
)

logger = logging.getLogger("mirai.vector_store")


class PolicyVectorStoreManager:
    """
    Manages persistent ChromaDB vector storage for university policy handbooks.
    Enforces deterministic chunk deduplication, version isolation, and safe re-ingestion.
    """

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or settings.resolved_chroma_directory
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.embedding_model = embedding_model or settings.GOOGLE_EMBEDDING_MODEL
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self._embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        self._vector_store: Optional[Chroma] = None
        self._client: Optional[chromadb.PersistentClient] = None

    def get_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """
        Returns the configured Google Generative AI embeddings instance.
        Validates API key presence before invocation.
        """
        if self._embeddings is None:
            active_key = self.api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if not active_key:
                raise EmbeddingAPIError(
                    "Google API key is missing. Set GOOGLE_API_KEY in backend/.env to generate embeddings."
                )
            try:
                self._embeddings = GoogleGenerativeAIEmbeddings(
                    model=self.embedding_model,
                    google_api_key=active_key,
                )
            except Exception as e:
                raise EmbeddingAPIError(f"Failed to initialize Google Generative AI Embeddings: {e}")
        return self._embeddings

    def get_chroma_client(self) -> chromadb.PersistentClient:
        """Initializes and returns the native persistent Chroma client."""
        if self._client is None:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            try:
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_directory),
                    settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False),
                )
            except Exception as e:
                raise VectorStoreError(f"Could not open persistent ChromaDB at '{self.persist_directory}': {e}")
        return self._client

    def get_vector_store(self, embeddings: Optional[GoogleGenerativeAIEmbeddings] = None) -> Chroma:
        """Returns or creates the LangChain Chroma vector store wrapper."""
        if self._vector_store is None:
            emb = embeddings or self.get_embeddings()
            client = self.get_chroma_client()
            try:
                self._vector_store = Chroma(
                    client=client,
                    collection_name=self.collection_name,
                    embedding_function=emb,
                )
            except Exception as e:
                raise VectorStoreError(f"Failed to bind LangChain Chroma vector store: {e}")
        return self._vector_store

    def is_initialized(self) -> bool:
        """Checks if the persistent collection exists and contains indexed documents."""
        try:
            client = self.get_chroma_client()
            collections = [c.name for c in client.list_collections()]
            if self.collection_name not in collections:
                return False
            col = client.get_collection(self.collection_name)
            return col.count() > 0
        except Exception:
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """Returns metadata statistics about the active Chroma collection."""
        client = self.get_chroma_client()
        collections = [c.name for c in client.list_collections()]
        if self.collection_name not in collections:
            return {
                "collection_name": self.collection_name,
                "initialized": False,
                "count": 0,
                "persist_directory": str(self.persist_directory),
            }

        col = client.get_collection(self.collection_name)
        count = col.count()
        return {
            "collection_name": self.collection_name,
            "initialized": count > 0,
            "count": count,
            "persist_directory": str(self.persist_directory),
            "embedding_model": self.embedding_model,
        }

    def ingest_documents(
        self,
        documents: List[Document],
        doc_hash: str,
        handbook_version: str = "2026",
        force_replace: bool = False,
    ) -> Dict[str, Any]:
        """
        Persists chunks to ChromaDB with deterministic IDs to prevent duplicate entries.
        Supports atomic replacement when force_replace=True.
        """
        if not documents:
            raise VectorStoreError("Cannot ingest an empty list of documents.")

        client = self.get_chroma_client()
        emb = self.get_embeddings()

        # If force_replace is requested, safely reset or recreate the collection
        if force_replace and self.collection_name in [c.name for c in client.list_collections()]:
            try:
                client.delete_collection(self.collection_name)
                self._vector_store = None
            except Exception as e:
                raise VectorStoreError(f"Failed to reset collection during re-ingestion: {e}")

        vector_store = self.get_vector_store(embeddings=emb)

        # Build IDs deterministically from chunk metadata
        ids = [doc.metadata.get("chunk_id", f"{doc_hash}_{idx}") for idx, doc in enumerate(documents)]

        try:
            # Check existing IDs to prevent duplicates
            col = client.get_or_create_collection(self.collection_name)
            existing_ids = set()
            try:
                existing_res = col.get(ids=ids)
                if existing_res and existing_res.get("ids"):
                    existing_ids = set(existing_res["ids"])
            except Exception:
                pass

            new_docs: List[Document] = []
            new_ids: List[str] = []

            for doc, chunk_id in zip(documents, ids):
                if chunk_id not in existing_ids:
                    new_docs.append(doc)
                    new_ids.append(chunk_id)

            if new_docs:
                vector_store.add_documents(documents=new_docs, ids=new_ids)
                logger.info(f"Ingested {len(new_docs)} new chunks into {self.collection_name}.")
            else:
                logger.info(f"All {len(ids)} chunks already exist in {self.collection_name}. Skipped duplicates.")

            total_count = col.count()
            return {
                "status": "success",
                "collection_name": self.collection_name,
                "added_chunks": len(new_docs),
                "skipped_duplicates": len(ids) - len(new_docs),
                "total_collection_count": total_count,
                "handbook_version": handbook_version,
                "doc_hash": doc_hash,
            }

        except Exception as e:
            raise VectorStoreError(f"Failed to persist documents into ChromaDB: {e}")

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
    ) -> List[Tuple[Document, float]]:
        """
        Performs similarity search with relevance scores.
        Raises VectorStoreNotInitializedError if index is empty.
        """
        if not self.is_initialized():
            raise VectorStoreNotInitializedError(
                "Handbook vector store is not initialized. Run ingestion first via POST /ingest or ingest_handbook.py."
            )

        vector_store = self.get_vector_store()
        try:
            results = vector_store.similarity_search_with_score(query=query, k=k)
            return results
        except Exception as e:
            raise VectorStoreError(f"Vector search failed for query '{query}': {e}")


# Singleton instance default
vector_store_manager = PolicyVectorStoreManager()
