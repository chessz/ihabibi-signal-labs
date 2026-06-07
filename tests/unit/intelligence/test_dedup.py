"""Unit tests for intelligence dedup and confirmation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from signals_lab.domain.intelligence import IntelligenceItem
from signals_lab.domain.intelligence_enums import (
    ContentRole,
    IntelligenceSourceType,
    ProviderTier,
)
from signals_lab.intelligence.dedup import merge_confirmations, title_dedup_key


def _item(title: str, provider: str, source: str, cred: str = "0.7") -> IntelligenceItem:
    return IntelligenceItem(
        external_id=f"{provider}:1",
        dedup_key=title_dedup_key(title),
        observed_at=datetime(2026, 6, 6, 12, 0, 0),
        provider=provider,
        provider_tier=ProviderTier.A,
        source_type=IntelligenceSourceType.NEWS,
        original_source=source,
        content_role=ContentRole.PRIMARY,
        title=title,
        credibility_score=Decimal(cred),
        confirming_providers=[provider],
    )


@pytest.mark.unit
def test_title_dedup_key_normalizes_punctuation() -> None:
    assert title_dedup_key("Bitcoin Hits $100K!") == title_dedup_key("bitcoin hits 100k")


@pytest.mark.unit
def test_merge_confirmations_groups_same_story() -> None:
    title = "SEC approves spot Ethereum ETF"
    expected_sources = 2
    items = [
        _item(title, "cryptocurrency_cv", "The Block", "0.72"),
        _item(title, "rss_fan_in", "CoinDesk", "0.85"),
    ]
    merged = merge_confirmations(items)
    assert len(merged) == 1
    assert merged[0].cross_source_confirmation_count == expected_sources
    assert set(merged[0].confirming_providers) == {"cryptocurrency_cv", "rss_fan_in"}
    assert merged[0].credibility_score == Decimal("0.85")
