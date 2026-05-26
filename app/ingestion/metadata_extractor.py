"""Metadata extraction for metadata-aware EV retrieval."""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from langchain_core.documents import Document

# Patterns aligned with study guide metadata dimensions
_VEHICLE_PATTERN = re.compile(
    r"\b(Model\s+[A-Z]\w+|EV-\d{3,4}|XYZ\s+\w+)\b", re.IGNORECASE
)
_FIRMWARE_PATTERN = re.compile(
    r"\b(firmware|FW|v?)(\d+\.\d+(?:\.\d+)?|OTA[-_]?\d+)\b", re.IGNORECASE
)
_DTC_PATTERN = re.compile(r"\b([PCBU][0-9A-F]{4})\b", re.IGNORECASE)
_CHARGING_PATTERN = re.compile(
    r"\b(CCS|CHAdeMO|Type\s*2|AC\s+Level\s*[12]|DC\s+Fast)\b", re.IGNORECASE
)
_CATEGORY_KEYWORDS = {
    "charging": ["charging", "charge port", "plug", "EVSE", "wallbox"],
    "battery": ["battery", "SOC", "BMS", "cell", "thermal"],
    "firmware": ["firmware", "OTA", "update", "software"],
    "infotainment": ["infotainment", "HMI", "screen", "display"],
    "diagnostics": ["DTC", "diagnostic", "trouble code", "scan tool"],
}


class MetadataExtractor:
    """Enrich chunks with vehicle, firmware, charging, and diagnostic metadata."""

    def extract_from_filename(self, filename: str) -> Dict[str, Any]:
        name = Path(filename).stem.lower()
        meta: Dict[str, Any] = {"source_file": filename, "document_source": "enterprise"}

        if "charging" in name or "ccs" in name:
            meta["diagnostic_category"] = "charging"
        elif "battery" in name or "dtc" in name:
            meta["diagnostic_category"] = "battery"
        elif "firmware" in name or "ota" in name:
            meta["diagnostic_category"] = "firmware"
        elif "infotainment" in name:
            meta["diagnostic_category"] = "infotainment"
        else:
            meta["diagnostic_category"] = "general"

        return meta

    def extract_from_text(self, text: str, base_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        meta = dict(base_meta or {})
        vehicle = _VEHICLE_PATTERN.search(text)
        if vehicle:
            meta["vehicle_model"] = vehicle.group(1)

        fw = _FIRMWARE_PATTERN.search(text)
        if fw:
            meta["firmware_version"] = fw.group(2)

        charging = _CHARGING_PATTERN.search(text)
        if charging:
            meta["charging_type"] = charging.group(1).upper().replace(" ", "")

        dtc = _DTC_PATTERN.search(text)
        if dtc:
            meta["dtc_code"] = dtc.group(1).upper()

        text_lower = text.lower()
        for category, keywords in _CATEGORY_KEYWORDS.items():
            if any(kw.lower() in text_lower for kw in keywords):
                meta.setdefault("diagnostic_category", category)
                break

        return meta

    def enrich_documents(
        self,
        documents: list[Document],
        overrides: Optional[Dict[str, Any]] = None,
    ) -> list[Document]:
        overrides = overrides or {}
        enriched: list[Document] = []
        for doc in documents:
            meta = self.extract_from_filename(doc.metadata.get("source_file", "unknown"))
            meta.update(self.extract_from_text(doc.page_content, meta))
            meta.update(overrides)
            meta.update({k: v for k, v in doc.metadata.items() if v})
            enriched.append(Document(page_content=doc.page_content, metadata=meta))
        return enriched
