"""Application-specific exceptions."""

from fastapi import HTTPException, status


class EVRAGException(Exception):
    """Base exception for EV RAG platform."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class IngestionError(EVRAGException):
    pass


class RetrievalError(EVRAGException):
    pass


class VectorStoreError(EVRAGException):
    pass


class GenerationError(EVRAGException):
    pass


def to_http_exception(exc: EVRAGException) -> HTTPException:
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, IngestionError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, RetrievalError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return HTTPException(status_code=status_code, detail={"message": exc.message, **exc.details})
