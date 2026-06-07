"""Title-based deduplication and cross-source confirmation."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from signals_lab.domain.intelligence import IntelligenceItem, RawIntelligenceRecord
from signals_lab.ingestion.normalizer import normalize_raw_record


def normalize_title(title: str) -> str:
    """Normalize title for dedup hashing."""
    text = title.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def title_dedup_key(title: str) -> str:
    normalized = normalize_title(title)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"title:{digest}"


def assign_dedup_keys(items: list[IntelligenceItem]) -> list[IntelligenceItem]:
    """Ensure every item has a stable dedup_key from normalized title."""
    updated: list[IntelligenceItem] = []
    for item in items:
        key = title_dedup_key(item.title)
        updated.append(item.model_copy(update={"dedup_key": key}))
    return updated


def merge_confirmations(items: list[IntelligenceItem]) -> list[IntelligenceItem]:
    """Group by dedup_key; boost confirmation count and merge provider lists."""
    groups: dict[str, list[IntelligenceItem]] = defaultdict(list)
    for item in items:
        groups[item.dedup_key].append(item)

    merged: list[IntelligenceItem] = []
    for _key, group in groups.items():
        canonical = max(group, key=lambda i: (i.credibility_score, i.observed_at))
        providers = sorted({i.provider for i in group})
        count = len(providers)
        merged.append(
            canonical.model_copy(
                update={
                    "cross_source_confirmation_count": count,
                    "confirming_providers": providers,
                    "entity_tags": sorted(set(canonical.entity_tags) | {s for i in group for s in i.entity_tags}),
                }
            )
        )
    return merged


def raw_to_items(raw_records: list[RawIntelligenceRecord]) -> list[IntelligenceItem]:
    """Normalize raw records to items with initial dedup keys."""
    items = [normalize_raw_record(r) for r in raw_records]
    return assign_dedup_keys(items)
