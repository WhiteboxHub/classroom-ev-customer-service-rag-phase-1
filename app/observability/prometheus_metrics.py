"""
prometheus_metrics.py
Prometheus metrics instrumentation for the EV RAG Platform.
Exposes: retrieval latency histograms, token counters, error rates,
reranker performance, vector store latency, ingestion throughput.
"""

from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class PrometheusMetrics:
    """
    Prometheus instrumentation for EV RAG operational monitoring.
    Gracefully degrades when prometheus_client is not installed.
    """

    def __init__(self):
        self._enabled = False
        self._init_metrics()

    def _init_metrics(self) -> None:
        try:
            from prometheus_client import Counter, Histogram, Gauge

            # Retrieval metrics
            self.retrieval_latency = Histogram(
                "ev_rag_retrieval_latency_seconds",
                "Retrieval pipeline latency in seconds",
                buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
                labelnames=["mode"],  # semantic, hybrid, bm25_fallback
            )
            self.retrieval_score = Histogram(
                "ev_rag_retrieval_score",
                "Top retrieval confidence score distribution",
                buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            )

            # Generation metrics
            self.generation_latency = Histogram(
                "ev_rag_generation_latency_seconds",
                "LLM generation latency in seconds",
                buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
            )
            self.token_usage_counter = Counter(
                "ev_rag_token_usage_total",
                "Total LLM tokens consumed",
                labelnames=["type"],  # prompt, completion
            )

            # Reranker metrics
            self.reranker_latency = Histogram(
                "ev_rag_reranker_latency_seconds",
                "Cross-encoder reranking latency in seconds",
                buckets=[0.05, 0.1, 0.25, 0.5, 1.0],
            )

            # Ingestion metrics
            self.ingestion_counter = Counter(
                "ev_rag_ingestion_chunks_total",
                "Total chunks ingested into the vector store",
                labelnames=["doc_category"],
            )
            self.ingestion_errors = Counter(
                "ev_rag_ingestion_errors_total",
                "Total ingestion failures",
            )

            # Cache metrics
            self.cache_hit_counter = Counter(
                "ev_rag_cache_hits_total",
                "Redis cache hits",
                labelnames=["namespace"],
            )
            self.cache_miss_counter = Counter(
                "ev_rag_cache_misses_total",
                "Redis cache misses",
                labelnames=["namespace"],
            )

            # API metrics
            self.api_request_counter = Counter(
                "ev_rag_api_requests_total",
                "Total API requests",
                labelnames=["endpoint", "method", "status"],
            )
            self.api_error_counter = Counter(
                "ev_rag_api_errors_total",
                "Total API errors",
                labelnames=["endpoint"],
            )

            # Hallucination guard
            self.hallucination_blocked_counter = Counter(
                "ev_rag_hallucination_blocked_total",
                "Responses blocked by hallucination guard",
            )

            self._enabled = True
            logger.info("prometheus_metrics_initialized")

        except ImportError:
            logger.warning("prometheus_not_installed", hint="pip install prometheus-client")
        except Exception as exc:
            logger.warning("prometheus_init_failed", error=str(exc))

    def record_retrieval(self, latency_s: float, mode: str, score: float) -> None:
        if not self._enabled:
            return
        self.retrieval_latency.labels(mode=mode).observe(latency_s)
        self.retrieval_score.observe(score)

    def record_generation(self, latency_s: float, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        if not self._enabled:
            return
        self.generation_latency.observe(latency_s)
        if prompt_tokens:
            self.token_usage_counter.labels(type="prompt").inc(prompt_tokens)
        if completion_tokens:
            self.token_usage_counter.labels(type="completion").inc(completion_tokens)

    def record_reranker(self, latency_s: float) -> None:
        if not self._enabled:
            return
        self.reranker_latency.observe(latency_s)

    def record_ingestion(self, chunks: int, doc_category: str = "unknown") -> None:
        if not self._enabled:
            return
        self.ingestion_counter.labels(doc_category=doc_category).inc(chunks)

    def record_cache_hit(self, namespace: str) -> None:
        if not self._enabled:
            return
        self.cache_hit_counter.labels(namespace=namespace).inc()

    def record_cache_miss(self, namespace: str) -> None:
        if not self._enabled:
            return
        self.cache_miss_counter.labels(namespace=namespace).inc()


# Singleton instance
prometheus_metrics = PrometheusMetrics()
