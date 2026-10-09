"""
Custom domain exceptions for MirAI Student Policy Advisor.
"""


class MirAIException(Exception):
    """Base exception for MirAI advisor application."""
    pass


class DocumentValidationError(MirAIException):
    """Raised when an ingested document fails validation (format, size, corrupt)."""
    pass


class EmptyDocumentError(DocumentValidationError):
    """Raised when a document has zero pages or zero extractable text."""
    pass


class ScannedPDFError(DocumentValidationError):
    """Raised when a PDF contains pages but no extractable textual content."""
    pass


class VectorStoreError(MirAIException):
    """Raised on ChromaDB or vector store operational failures."""
    pass


class VectorStoreNotInitializedError(VectorStoreError):
    """Raised when querying a vector store before any handbook has been ingested."""
    pass


class EmbeddingAPIError(MirAIException):
    """Raised when Google Generative AI embeddings fail or quota is exhausted."""
    pass


class ModelUnavailableError(MirAIException):
    """Raised when the specified Google Gemini model is not accessible."""
    pass


class RetrievalError(MirAIException):
    """Raised during MultiQueryRetriever or search failures."""
    pass


class GenerationError(MirAIException):
    """Raised when the LCEL generation chain fails to produce a response."""
    pass
