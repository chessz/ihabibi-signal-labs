"""Datetime utilities for signals-lab."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def isoformat(dt: datetime) -> str:
    """Format datetime as ISO 8601 string."""
    return dt.isoformat()