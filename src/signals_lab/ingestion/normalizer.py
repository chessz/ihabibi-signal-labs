"""Normalize RawIntelligenceRecord → IntelligenceItem."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from signals_lab.domain.intelligence import IntelligenceItem, RawIntelligenceRecord
from signals_lab.intelligence.config_loader import get_intelligence_config


def extract_asset_tags(text: str, hints: list[str] | None = None) -> list[str]:
    """Extract asset tickers from text using config keyword map."""
    config = get_intelligence_config()
    combined = f"{text} {' '.join(hints or [])}".lower()
    tags: list[str] = []
    for ticker, keywords in config.asset_keywords.items():
        if hints and ticker in hints:
            tags.append(ticker)
            continue
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw.lower())}\b", combined):
                tags.append(ticker)
                break
    return sorted(set(tags))


def extract_entity_tags(text: str) -> list[str]:
    """Lightweight entity hints from capitalized phrases and known names."""
    entities: set[str] = set()
    known = [
        "SEC",
        "Binance",
        "Coinbase",
        "BlackRock",
        "Fidelity",
        "Ethereum Foundation",
        "Fed",
        "ECB",
    ]
    for name in known:
        if name.lower() in text.lower():
            entities.add(name)
    return sorted(entities)


def normalize_raw_record(raw: RawIntelligenceRecord) -> IntelligenceItem:
    text = f"{raw.title} {raw.body}"
    assets = extract_asset_tags(text, raw.asset_hints)
    entities = sorted(set(extract_entity_tags(text)) | set(raw.entity_hints))

    return IntelligenceItem(
        external_id=raw.external_id,
        dedup_key=raw.external_id,
        observed_at=raw.observed_at,
        ingested_at=datetime.utcnow(),
        provider=raw.provider,
        provider_tier=raw.provider_tier,
        source_type=raw.source_type,
        original_source=raw.original_source,
        content_role=raw.content_role,
        url=raw.url,
        message_id=raw.message_id,
        title=raw.title.strip(),
        body=raw.body.strip(),
        language=raw.language,
        asset_tags=assets,
        entity_tags=entities,
        credibility_score=Decimal(str(raw.base_credibility)),
        confirming_providers=[raw.provider],
        cross_source_confirmation_count=1,
        enrichment={"raw_source_type": raw.source_type.value},
    )
