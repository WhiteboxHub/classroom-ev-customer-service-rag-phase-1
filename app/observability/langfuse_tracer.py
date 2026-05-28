"""
langfuse_tracer.py
Langfuse observability integration for the EV RAG platform.
Tracks: LLM calls, retrieval traces, reranker spans, token usage, latency.
Aligns with EV Study Guide Section 5.18 — Observability Architecture.
"""

import functools
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LangfuseTracer:
    """
    Langfuse integration for EV RAG LLM observability.
    Gracefully degrades when Langfuse is not configured.
    """

    def __init__(self):
        self._langfuse = None
        self._enabled = settings.langfuse_enabled
        if self._enabled:
            self._init_langfuse()

    def _init_langfuse(self) -> None:
        try:
            from langfuse import Langfuse
            self._langfuse = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            logger.info("langfuse_initialized", host=settings.langfuse_host)
        except ImportError:
            logger.warning("langfuse_not_installed", hint="pip install langfuse")
            self._enabled = False
        except Exception as exc:
            logger.warning("langfuse_init_failed", error=str(exc))
            self._enabled = False

    @contextmanager
    def trace_retrieval(
        self,
        query: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Context manager to trace an EV RAG retrieval operation.
        Records query, latency, and retrieved chunk count.
        """
        if not self._enabled or not self._langfuse:
            yield None
            return

        trace = self._langfuse.trace(
            name="ev_rag_retrieval",
            input={"query": query},
            session_id=session_id,
            metadata=metadata or {},
        )
        span = trace.span(
            name="hybrid_retrieval",
            input={"query": query},
        )
        start = time.perf_counter()
        try:
            yield span
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            span.end(output={"latency_ms": round(latency_ms, 2)})

    @contextmanager
    def trace_generation(
        self,
        query: str,
        model: str,
        session_id: Optional[str] = None,
    ):
        """
        Context manager to trace an LLM generation call.
        Records prompt tokens, completion tokens, latency, model.
        """
        if not self._enabled or not self._langfuse:
            yield None
            return

        trace = self._langfuse.trace(
            name="ev_rag_generation",
            input={"query": query},
            session_id=session_id,
        )
        generation = trace.generation(
            name="openai_chat_completion",
            model=model,
            input=[{"role": "user", "content": query}],
        )
        start = time.perf_counter()
        try:
            yield generation
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            generation.end(
                output={"latency_ms": round(latency_ms, 2)},
            )

    def record_feedback(
        self,
        trace_id: str,
        rating: int,
        comment: str = "",
    ) -> None:
        """Record technician feedback on a RAG response quality."""
        if not self._enabled or not self._langfuse:
            return
        try:
            self._langfuse.score(
                trace_id=trace_id,
                name="technician_rating",
                value=rating,
                comment=comment,
            )
        except Exception as exc:
            logger.warning("langfuse_feedback_failed", error=str(exc))

    def flush(self) -> None:
        """Flush pending Langfuse events."""
        if self._enabled and self._langfuse:
            self._langfuse.flush()


# Singleton tracer instance
langfuse_tracer = LangfuseTracer()
