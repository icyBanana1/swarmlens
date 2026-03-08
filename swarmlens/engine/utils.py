from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any

WORD_RE = re.compile(r"[a-zA-Z0-9_#@']+")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def normalize_text(text: str) -> str:
    return " ".join(token.lower() for token in WORD_RE.findall(text or ""))


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in WORD_RE.findall(text or "")]


def jaccard_similarity(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def bucket_time(dt: datetime | None, seconds: int = 120) -> str:
    if dt is None:
        return "unknown"
    bucket = int(dt.timestamp()) // seconds * seconds
    return datetime.fromtimestamp(bucket, tz=dt.tzinfo).isoformat()


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def grade(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.45:
        return "medium"
    if score >= 0.25:
        return "low"
    return "minimal"
