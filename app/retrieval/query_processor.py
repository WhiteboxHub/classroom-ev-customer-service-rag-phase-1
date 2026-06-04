"""Query cleaning, validation, and intent-aware preprocessing."""

import re
from typing import Dict, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

EV_SPELLING_MAP = {
    "chargng": "charging",
    "batery": "battery",
    "firmwaree": "firmware",
    "ota update": "OTA update",
    "dc fast": "DC fast charging",
    "level 2": "AC Level 2",
}

INTENT_PATTERNS = {
    "charging": re.compile(r"\b(charg|evse|plug|ccs|chademo)\w*", re.I),
    "firmware": re.compile(r"\b(firmware|ota|update|software)\w*", re.I),
    "battery": re.compile(r"\b(battery|bms|soc|cell)\w*", re.I),
    "diagnostics": re.compile(r"\b(dtc|p0|u0|c0|b0|diagnostic)\w*", re.I),
    "infotainment": re.compile(r"\b(screen|hmi|display|infotainment)\w*", re.I),
}

PII_PATTERNS = [
    (re.compile(r"\bVIN[:\s]*[A-HJ-NPR-Z0-9]{17}\b", re.I), "[VIN_REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[ID_REDACTED]"),
]


class QueryProcessor:
    """Preprocess support queries before embedding and retrieval."""

    def process(self, query: str) -> Tuple[str, Dict[str, str]]:
        cleaned = query.strip()
        for pattern, replacement in PII_PATTERNS:
            cleaned = pattern.sub(replacement, cleaned)

        lower = cleaned.lower()
        for wrong, correct in EV_SPELLING_MAP.items():
            if wrong in lower:
                cleaned = re.sub(re.escape(wrong), correct, cleaned, flags=re.IGNORECASE)

        intent = self._classify_intent(cleaned)
        meta: Dict[str, str] = {}
        if intent:
            meta["diagnostic_category"] = intent

        logger.debug("query_processed", intent=intent, length=len(cleaned))
        return cleaned, meta

    def _classify_intent(self, query: str) -> str:
        for intent, pattern in INTENT_PATTERNS.items():
            if pattern.search(query):
                return intent
        return ""

    def format_retrieval_instruction(self, query: str) -> str:
        """Instruction-based query formatting for improved semantic retrieval."""
        return (
            f"Retrieve EV troubleshooting procedures related to: {query}"
        )
