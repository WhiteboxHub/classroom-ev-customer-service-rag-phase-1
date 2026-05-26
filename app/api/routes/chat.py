"""Grounded chat API for multi-turn EV troubleshooting."""

from fastapi import APIRouter

from app.api.dependencies import get_rag_service
from app.api.schemas.requests import ChatRequest
from app.api.schemas.responses import ChatMessage, ChatResponse
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    metadata = request.metadata_filter.model_dump(exclude_none=True) if request.metadata_filter else None
    service = get_rag_service()
    result = service.chat(
        query=request.query,
        session_id=request.session_id,
        top_k=request.top_k,
        use_hybrid=request.use_hybrid,
        use_rerank=request.use_rerank,
        metadata_filter=metadata,
    )

    from app.api.schemas.responses import SourceChunk

    sources = [SourceChunk(**s) for s in result["sources"]]
    history = [ChatMessage(**m) for m in result.get("history", [])]

    return ChatResponse(
        session_id=result["session_id"],
        answer=result["answer"],
        sources=sources if request.include_sources else [],
        citations=result["citations"],
        latency_ms=result["latency_ms"],
        grounded=result["grounded"],
        history=history,
    )
