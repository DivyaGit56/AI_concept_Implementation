"""Utility helpers."""

import re
import uuid
from datetime import datetime, timezone
from typing import Any


def generate_id(prefix: str = "") -> str:
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}{uid}" if prefix else uid


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    return text.strip()


def truncate_text(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    if doc is None:
        return {}
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    return result
