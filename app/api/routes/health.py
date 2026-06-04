"""Health check endpoints."""

from fastapi import APIRouter

from app import __version__
from app.api.dependencies import get_cache, get_vector_store
from app.api.schemas.responses import HealthResponse
from app.observability.metrics import metrics_collector
from app.utils.helpers import utc_now_iso

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    milvus = get_vector_store().health_check()
    redis_status = get_cache().health_check()
    status = "healthy" if milvus == "healthy" else "degraded"
    return HealthResponse(
        status=status,
        version=__version__,
        milvus=milvus,
        redis=redis_status,
        timestamp=utc_now_iso(),
    )


@router.get("/metrics")
async def metrics() -> dict:
    return metrics_collector.summary()
