"""Request logging and latency tracking middleware."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        start = time.perf_counter()
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(round(latency_ms, 2))
        logger.info(
            "request_completed",
            request_id=request_id,
            status=response.status_code,
            latency_ms=round(latency_ms, 2),
        )
        return response
