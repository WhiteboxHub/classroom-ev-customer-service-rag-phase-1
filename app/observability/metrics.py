"""Retrieval and generation latency metrics."""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricsCollector:
    """In-memory operational metrics for observability."""

    retrieval_latencies: List[float] = field(default_factory=list)
    generation_latencies: List[float] = field(default_factory=list)
    ingestion_counts: int = 0

    @contextmanager
    def track(self, operation: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if operation == "retrieval":
                self.retrieval_latencies.append(elapsed_ms)
            elif operation == "generation":
                self.generation_latencies.append(elapsed_ms)
            logger.info(f"{operation}_latency_ms", latency_ms=round(elapsed_ms, 2))

    def record_ingestion(self, chunks: int) -> None:
        self.ingestion_counts += chunks

    def summary(self) -> Dict[str, float]:
        def avg(values: List[float]) -> float:
            return round(sum(values) / len(values), 2) if values else 0.0

        return {
            "avg_retrieval_latency_ms": avg(self.retrieval_latencies[-100:]),
            "avg_generation_latency_ms": avg(self.generation_latencies[-100:]),
            "total_chunks_ingested": float(self.ingestion_counts),
        }


metrics_collector = MetricsCollector()
