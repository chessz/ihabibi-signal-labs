"""Novelty scoring — higher for fresh unique narratives in batch."""

from __future__ import annotations

from decimal import Decimal

from signals_lab.domain.intelligence import IntelligenceItem
from signals_lab.intelligence.dedup import normalize_title

_DUPLICATE_NOVELTY_COUNT = 2


def score_novelty_batch(items: list[IntelligenceItem]) -> list[IntelligenceItem]:
    """Items with unique normalized titles in batch get higher novelty."""
    title_counts: dict[str, int] = {}
    for item in items:
        key = normalize_title(item.title)
        title_counts[key] = title_counts.get(key, 0) + 1

    scored: list[IntelligenceItem] = []
    for item in items:
        key = normalize_title(item.title)
        count = title_counts.get(key, 1)
        if count == 1:
            novelty = Decimal("0.85")
        elif count == _DUPLICATE_NOVELTY_COUNT:
            novelty = Decimal("0.55")
        else:
            novelty = Decimal("0.35")
        scored.append(item.model_copy(update={"novelty_score": novelty}))
    return scored
