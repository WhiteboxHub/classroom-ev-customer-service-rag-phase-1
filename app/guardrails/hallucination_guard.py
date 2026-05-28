"""
hallucination_guard.py
Detects and prevents hallucinated responses in the EV RAG platform.
A response is considered grounded if it references only retrieved source content.
Aligns with EV Study Guide Section 5.16 — Retrieval Safety Patterns.
"""

import re
from typing import Any, Dict, List, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Markers that indicate LLM is reasoning beyond retrieved context
HALLUCINATION_SIGNALS = [
    r"in general\b",
    r"typically\b",
    r"usually\b",
    r"I believe\b",
    r"I think\b",
    r"as far as I know",
    r"from my knowledge",
    r"you should consult",
    r"I cannot find",
    r"not mentioned in",
]

# Phrases that confirm the response IS grounded in retrieved context
GROUNDING_SIGNALS = [
    r"\[Source \d+\]",
    r"according to",
    r"as stated in",
    r"the documentation states",
    r"per the service manual",
    r"the DTC catalog indicates",
    r"firmware release notes",
]


class HallucinationGuard:
    """
    Post-generation hallucination detector for EV troubleshooting responses.
    Validates that the answer is grounded in retrieved source chunks.
    """

    def __init__(
        self,
        hallucination_threshold: float = 0.4,
        grounding_threshold: float = 0.3,
    ):
        self.hallucination_threshold = hallucination_threshold
        self.grounding_threshold = grounding_threshold

    def check(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
    ) -> Tuple[bool, float, str]:
        """
        Check if an answer is grounded.
        Returns: (is_grounded, confidence_score, reason)
        """
        if not sources:
            logger.warning("hallucination_guard_no_sources")
            return False, 0.0, "no_retrieved_sources"

        answer_lower = answer.lower()

        # Count hallucination signals
        hall_count = sum(
            1 for pattern in HALLUCINATION_SIGNALS if re.search(pattern, answer_lower)
        )

        # Count grounding signals
        ground_count = sum(
            1 for pattern in GROUNDING_SIGNALS if re.search(pattern, answer_lower)
        )

        # Check answer references source content
        source_coverage = self._check_source_coverage(answer, sources)

        # Composite grounding score
        hall_ratio = hall_count / max(len(HALLUCINATION_SIGNALS), 1)
        ground_ratio = ground_count / max(len(GROUNDING_SIGNALS), 1)
        confidence = (ground_ratio + source_coverage * 0.5) - (hall_ratio * 0.8)
        confidence = max(0.0, min(1.0, confidence))

        is_grounded = confidence >= self.grounding_threshold and hall_ratio < self.hallucination_threshold

        reason = "grounded" if is_grounded else f"low_confidence:{confidence:.2f}"
        logger.info(
            "hallucination_check",
            is_grounded=is_grounded,
            confidence=round(confidence, 3),
            hall_signals=hall_count,
            ground_signals=ground_count,
        )
        return is_grounded, confidence, reason

    @staticmethod
    def _check_source_coverage(answer: str, sources: List[Dict[str, Any]]) -> float:
        """Check what fraction of sources are referenced in the answer."""
        if not sources:
            return 0.0
        referenced = 0
        for idx in range(1, len(sources) + 1):
            if f"[Source {idx}]" in answer or f"source {idx}" in answer.lower():
                referenced += 1
        return referenced / len(sources)
