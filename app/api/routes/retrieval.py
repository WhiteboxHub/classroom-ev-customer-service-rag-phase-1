"""Retrieval-only API endpoints."""

from fastapi import APIRouter

from app.api.dependencies import get_rag_service
from app.api.schemas.requests import RetrievalRequest
from app.api.schemas.responses import RetrievalResponse
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/retrieve", tags=["Retrieval"])


@router.post("", response_model=RetrievalResponse)
async def retrieve_documents(request: RetrievalRequest) -> RetrievalResponse:
    metadata = request.metadata_filter.model_dump(exclude_none=True) if request.metadata_filter else None
    service = get_rag_service()
    sources, latency_ms, mode = service.retrieve(
        query=request.query,
        top_k=request.top_k,
        use_hybrid=request.use_hybrid,
        use_rerank=request.use_rerank,
        metadata_filter=metadata,
    )
    return RetrievalResponse(
        query=request.query,
        sources=sources,
        latency_ms=latency_ms,
        retrieval_mode=mode,
    )
