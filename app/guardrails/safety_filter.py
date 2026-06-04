"""
safety_filter.py
Safety filter for EV RAG responses.
Prevents dangerous repair instructions without proper safety warnings.
Enforces HV (high-voltage) safety disclaimers for battery/charging work.
"""

import re
from typing import Any, Dict, List, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns requiring mandatory HV safety disclaimer
HV_SAFETY_TRIGGERS = [
    r"high.?voltage",
    r"\b400V\b",
    r"\b800V\b",
    r"battery pack",
    r"HV bus",
    r"DC fast charge",
    r"battery disconnect",
    r"manual service disconnect",
    r"MSD",
    r"fuse removal",
]

HV_SAFETY_DISCLAIMER = (
    "\n\n⚠️ **HIGH-VOLTAGE SAFETY WARNING**: This procedure involves high-voltage "
    "components. Only trained and certified EV technicians with appropriate PPE "
    "(insulated gloves ≥1000V rated, face shield, HV-rated tools) should perform this work. "
    "Ensure the vehicle is powered off and HV system is isolated before proceeding. "
    "Follow all OEM safety protocols."
)

# Queries that should never be answered (escalate to certified tech)
BLOCKED_PATTERNS = [
    r"bypass.*safety",
    r"disable.*BMS",
    r"override.*thermal.*protection",
    r"remove.*battery.*fire",
]


class SafetyFilter:
    """
    Post-generation safety filter for EV troubleshooting responses.
    Injects HV safety disclaimers and blocks dangerous instructions.
    """

    def apply(self, query: str, answer: str) -> Tuple[str, bool, str]:
        """
        Apply safety filters to an EV RAG answer.
        Returns: (filtered_answer, is_safe, safety_action)
        """
        query_lower = query.lower()
        answer_lower = answer.lower()

        # Check for blocked dangerous patterns in query
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, query_lower):
                blocked_response = (
                    "This query involves safety-critical EV procedures that cannot be "
                    "answered through this system. Please consult a certified EV technician "
                    "and refer to the OEM service manual. Safety first."
                )
                logger.warning("safety_filter_blocked", pattern=pattern, query=query[:80])
                return blocked_response, False, f"blocked:{pattern}"

        # Check if response involves HV components — inject disclaimer
        hv_triggered = any(
            re.search(p, answer_lower) for p in HV_SAFETY_TRIGGERS
        )
        if hv_triggered and HV_SAFETY_DISCLAIMER not in answer:
            answer = answer + HV_SAFETY_DISCLAIMER
            logger.info("safety_disclaimer_injected")
            return answer, True, "hv_disclaimer_added"

        return answer, True, "no_action"
