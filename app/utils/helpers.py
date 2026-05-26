"""Reusable utility functions."""

import hashlib
import re
import uuid
from datetime import datetime, timezone


def generate_id(prefix: str = "ev") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w.\-]", "_", name)
    return cleaned or "document"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
