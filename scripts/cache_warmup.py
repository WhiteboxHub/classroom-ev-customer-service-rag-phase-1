"""
cache_warmup.py
Pre-warms Redis cache with high-frequency EV DTC queries.
Reduces P99 latency for common troubleshooting queries.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cache.redis_cache import RedisCache
from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService
from app.retrieval.rag_service import RAGService

logger = get_logger(__name__)

# High-frequency EV troubleshooting queries to pre-warm
WARM_QUERIES = [
    "What does DTC P0A80 mean?",
    "Battery thermal warning BMS_TEMP_HIGH",
    "CCS charging not starting P1E00",
    "OTA update failed OTA_INSTALL_FAIL_3",
    "Vehicle not charging after firmware update",
    "U0100 CAN bus communication failure",
    "AC Level 2 charging slow or not starting",
    "How to perform manual service disconnect MSD",
    "Battery state of health SOH diagnostic",
    "Infotainment screen blank B2AAA",
    "DC fast charging rate reduced",
    "Firmware 4.2.1 release notes",
    "P0A94 DC DC converter performance",
    "Cell voltage spread out of range",
    "Pre-conditioning battery before fast charging",
]


def warm_cache(queries: list = None) -> dict:
    """Pre-populate Redis cache with EV troubleshooting query results."""
    queries = queries or WARM_QUERIES
    rag_service = RAGService()
    
    warmed = 0
    errors = 0
    
    print(f"Warming cache with {len(queries)} EV queries...")
    
    for query in queries:
        try:
            print(f"  Warming: {query[:60]}...")
            sources, latency_ms, mode = rag_service.retrieve(query, top_k=5)
            print(f"    Cached {len(sources)} sources ({latency_ms:.0f}ms)")
            warmed += 1
        except Exception as exc:
            print(f"    ERROR: {exc}")
            errors += 1
    
    result = {"total": len(queries), "warmed": warmed, "errors": errors}
    print(f"\nCache warmup complete: {warmed}/{len(queries)} queries cached")
    logger.info("cache_warmup_complete", **result)
    return result


if __name__ == "__main__":
    warm_cache()
