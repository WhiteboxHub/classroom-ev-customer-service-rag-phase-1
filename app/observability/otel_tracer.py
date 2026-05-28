"""
otel_tracer.py
OpenTelemetry distributed tracing for the EV RAG Platform.
Exports traces to OTel Collector (Jaeger / CloudWatch / Grafana Tempo).
Aligns with EV Study Guide Section 5.18.3 — Distributed Tracing.
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OTelTracer:
    """
    OpenTelemetry tracer for the EV RAG platform.
    Gracefully degrades when OTel SDK is not installed or endpoint unreachable.
    """

    def __init__(self):
        self._tracer = None
        self._enabled = settings.otel_enabled
        if self._enabled:
            self._init_otel()

    def _init_otel(self) -> None:
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({
                "service.name": settings.otel_service_name,
                "service.version": "1.0.0",
                "deployment.environment": "production",
            })
            provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(settings.otel_service_name)
            logger.info("otel_initialized", endpoint=settings.otel_exporter_endpoint)
        except ImportError:
            logger.warning("otel_not_installed", hint="pip install opentelemetry-sdk opentelemetry-exporter-otlp")
            self._enabled = False
        except Exception as exc:
            logger.warning("otel_init_failed", error=str(exc))
            self._enabled = False

    @contextmanager
    def span(self, operation: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Context manager to create an OTel span for an EV RAG operation.
        Operations: retrieval, reranking, generation, ingestion, embedding.
        """
        if not self._enabled or not self._tracer:
            yield None
            return

        with self._tracer.start_as_current_span(operation) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            try:
                yield span
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(self._get_error_status())
                raise

    @staticmethod
    def _get_error_status():
        try:
            from opentelemetry.trace import StatusCode
            return StatusCode.ERROR
        except ImportError:
            return None


# Singleton OTel tracer
otel_tracer = OTelTracer()
