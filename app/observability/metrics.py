"""
metrics.py
In-memory metrics collector for the EV RAG Platform.
Provides lightweight request-level metrics when Prometheus is not available.
Used as a fallback and for API /metrics endpoint.
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricsSample:
    """Single metrics sample with timestamp."""
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


class InMemoryMetricsCollector:
    """
    Lightweight in-memory metrics collector for the EV RAG Platform.
    Tracks retrieval latency, generation latency, cache performance,
    ingestion throughput, and error counts without external dependencies.
    Thread-safe via lock.
    """

    def __init__(self, max_samples: int = 10000):
        self._lock = threading.Lock()
        self._max_samples = max_samples

        # Counters
        self._counters: Dict[str, float] = defaultdict(float)
        # Histograms (store raw samples for percentile calculation)
        self._histograms: Dict[str, List[MetricsSample]] = defaultdict(list)
        # Gauges
        self._gauges: Dict[str, float] = defaultdict(float)

        # Boot time for uptime calculation
        self._start_time = time.time()

    # ──────────────────────────────────────────────────────────
    # Counter Operations
    # ──────────────────────────────────────────────────────────

    def inc_counter(self, name: str, value: float = 1.0) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value

    def get_counter(self, name: str) -> float:
        """Get current counter value."""
        with self._lock:
            return self._counters.get(name, 0.0)

    # ──────────────────────────────────────────────────────────
    # Histogram Operations
    # ──────────────────────────────────────────────────────────

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record an observation (e.g., latency) in a histogram."""
        sample = MetricsSample(value=value, labels=labels or {})
        with self._lock:
            samples = self._histograms[name]
            samples.append(sample)
            # Trim if over max
            if len(samples) > self._max_samples:
                self._histograms[name] = samples[-self._max_samples:]

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics: count, sum, avg, p50, p95, p99."""
        with self._lock:
            samples = self._histograms.get(name, [])

        if not samples:
            return {"count": 0, "sum": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}

        values = sorted([s.value for s in samples])
        n = len(values)
        total = sum(values)

        return {
            "count": n,
            "sum": round(total, 4),
            "avg": round(total / n, 4),
            "min": round(values[0], 4),
            "max": round(values[-1], 4),
            "p50": round(values[int(n * 0.50)], 4),
            "p95": round(values[min(int(n * 0.95), n - 1)], 4),
            "p99": round(values[min(int(n * 0.99), n - 1)], 4),
        }

    # ──────────────────────────────────────────────────────────
    # Gauge Operations
    # ──────────────────────────────────────────────────────────

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric to a specific value."""
        with self._lock:
            self._gauges[name] = value

    def get_gauge(self, name: str) -> float:
        """Get current gauge value."""
        with self._lock:
            return self._gauges.get(name, 0.0)

    # ──────────────────────────────────────────────────────────
    # EV RAG Convenience Methods
    # ──────────────────────────────────────────────────────────

    def record_retrieval(self, latency_s: float, mode: str = "hybrid", score: float = 0.0) -> None:
        """Record a retrieval operation."""
        self.observe("retrieval_latency_seconds", latency_s, {"mode": mode})
        self.observe("retrieval_top_score", score)
        self.inc_counter("retrieval_requests_total")

    def record_generation(self, latency_s: float, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Record an LLM generation operation."""
        self.observe("generation_latency_seconds", latency_s)
        self.inc_counter("generation_requests_total")
        self.inc_counter("token_usage_prompt", prompt_tokens)
        self.inc_counter("token_usage_completion", completion_tokens)

    def record_cache_hit(self, namespace: str = "query") -> None:
        self.inc_counter(f"cache_hits_{namespace}")

    def record_cache_miss(self, namespace: str = "query") -> None:
        self.inc_counter(f"cache_misses_{namespace}")

    def record_ingestion(self, chunks: int, category: str = "unknown") -> None:
        self.inc_counter("ingestion_chunks_total", chunks)
        self.inc_counter(f"ingestion_chunks_{category}", chunks)

    def record_error(self, component: str) -> None:
        self.inc_counter(f"errors_{component}")
        self.inc_counter("errors_total")

    def record_hallucination_blocked(self) -> None:
        self.inc_counter("hallucination_blocked_total")

    # ──────────────────────────────────────────────────────────
    # Export / API
    # ──────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        """
        Return a full metrics snapshot for the /api/v1/metrics endpoint.
        """
        with self._lock:
            counters = dict(self._counters)
            gauges = dict(self._gauges)

        histogram_names = [
            "retrieval_latency_seconds",
            "retrieval_top_score",
            "generation_latency_seconds",
        ]

        histograms = {}
        for name in histogram_names:
            histograms[name] = self.get_histogram_stats(name)

        return {
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "counters": counters,
            "gauges": gauges,
            "histograms": histograms,
        }

    def reset(self) -> None:
        """Reset all metrics. Used for testing."""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()
            self._start_time = time.time()


# Singleton instance
metrics_collector = InMemoryMetricsCollector()
