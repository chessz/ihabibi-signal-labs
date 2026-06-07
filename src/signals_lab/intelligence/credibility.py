"""Rules-based credibility scoring — Tier C (no ML)."""

from __future__ import annotations

from decimal import Decimal

from signals_lab.domain.intelligence import IntelligenceItem
from signals_lab.domain.intelligence_enums import ContentRole
from signals_lab.intelligence.config_loader import get_intelligence_config

_MIN_CONFIRMATION_SOURCES = 2
_MIN_TITLE_LENGTH = 20
_MAX_EXCLAMATION_MARKS = 2


def _clickbait_patterns() -> list[str]:
    return get_intelligence_config().clickbait_patterns


def score_credibility(item: IntelligenceItem, base: Decimal | None = None) -> Decimal:
    """Compute credibility from base prior, content role, and confirmation."""
    start = base if base is not None else item.credibility_score
    score = start

    if item.content_role == ContentRole.PRIMARY:
        score += Decimal("0.05")
    elif item.content_role == ContentRole.REPOST:
        score -= Decimal("0.15")
    elif item.content_role == ContentRole.RUMOR:
        score -= Decimal("0.25")
    elif item.content_role == ContentRole.COMMENTARY:
        score -= Decimal("0.05")

    if item.cross_source_confirmation_count >= _MIN_CONFIRMATION_SOURCES:
        score += Decimal("0.05") * Decimal(min(item.cross_source_confirmation_count - 1, 3))

    return max(Decimal("0"), min(Decimal("1"), score))


def apply_credibility_penalties(item: IntelligenceItem) -> IntelligenceItem:
    """Apply clickbait and low-quality title penalties."""
    score = item.credibility_score
    title_lower = item.title.lower()

    for pattern in _clickbait_patterns():
        if pattern.lower() in title_lower:
            score -= Decimal("0.12")
            break

    if title_lower.endswith("?!") or title_lower.count("!") >= _MAX_EXCLAMATION_MARKS:
        score -= Decimal("0.05")

    if len(item.title) < _MIN_TITLE_LENGTH:
        score -= Decimal("0.03")

    score = max(Decimal("0"), min(Decimal("1"), score))
    return item.model_copy(update={"credibility_score": score})
