"""
threshold_guard.py
Retrieval confidence threshold enforcement for the EV RAG platform.
Prevents low-confidence retrievals from being used for generation.
Aligns with EV Study Guide Section 5.16.2 — Fallback Logic.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

FALLBACK_RESPONSE = (
    "I could not find sufficiently relevant EV troubleshooting documentation for your query. "
    "The retrieved context confidence is below the safety threshold.\n\n"
    "**Recommended actions:**\n"
    "1. Refine your query with specific DTC codes, firmware version, or vehicle model.\n"
    "2. Upload additional service manuals or DTC catalogs via the ingestion API.\n"
    "3. Contact your regional EV support specialist for urgent issues.\n"
    "4. Reference the OEM service portal directly for critical safety procedures."
)


class ThresholdGuard:
    """
    Enforces minimum retrieval confidence before allowing LLM generation.
    Returns a structured fallback response when confidence is too low.
    """

    def __init__(
        self,
        score_threshold: Optional[float] = None,
        min_sources: int = 1,
    ):
        self.score_threshold = score_threshold or settings.retrieval_score_threshold
        self.min_sources = min_sources

    def validate(
        self,
        sources: List[Dict[str, Any]],
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate retrieval results against confidence thresholds.
        Returns: (passes, reason, fallback_response_or_None)
        """
        if not sources:
            logger.warning("threshold_guard_no_sources")
            return False, "no_sources", FALLBACK_RESPONSE

        if len(sources) < self.min_sources:
            logger.warning("threshold_guard_too_few_sources", count=len(sources))
            return False, "insufficient_sources", FALLBACK_RESPONSE

        top_score = max(s.get("score", 0.0) for s in sources)
        avg_score = sum(s.get("score", 0.0) for s in sources) / len(sources)

        if top_score < self.score_threshold:
            logger.warning(
                "threshold_guard_low_confidence",
                top_score=round(top_score, 3),
                threshold=self.score_threshold,
            )
            return (
                False,
                f"low_confidence:{top_score:.3f}<{self.score_threshold}",
                FALLBACK_RESPONSE,
            )

        logger.debug(
            "threshold_guard_passed",
            top_score=round(top_score, 3),
            avg_score=round(avg_score, 3),
        )
        return True, "passed", None
