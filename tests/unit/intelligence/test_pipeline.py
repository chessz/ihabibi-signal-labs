"""Unit tests for intelligence pipeline."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from signals_lab.domain.intelligence import RawIntelligenceRecord
from signals_lab.domain.intelligence_enums import (
    ContentRole,
    IntelligenceSourceType,
    ProviderTier,
)
from signals_lab.intelligence.engine import IntelligencePipeline


@pytest.mark.unit
def test_pipeline_deduplicates_and_scores() -> None:
    raw = [
        RawIntelligenceRecord(
            external_id="cv:1",
            provider="cryptocurrency_cv",
            provider_tier=ProviderTier.A,
            source_type=IntelligenceSourceType.NEWS,
            original_source="CoinDesk",
            observed_at=datetime(2026, 6, 6, 12, 0, 0),
            title="Bitcoin ETF sees record inflows",
            body="Institutional demand continues.",
            base_credibility=Decimal("0.72"),
            content_role=ContentRole.PRIMARY,
            asset_hints=["BTC"],
        ),
        RawIntelligenceRecord(
            external_id="rss:1",
            provider="rss_fan_in",
            provider_tier=ProviderTier.A,
            source_type=IntelligenceSourceType.NEWS,
            original_source="CoinDesk",
            observed_at=datetime(2026, 6, 6, 12, 5, 0),
            title="Bitcoin ETF sees record inflows",
            body="Same story syndicated.",
            base_credibility=Decimal("0.85"),
            content_role=ContentRole.PRIMARY,
            asset_hints=["BTC"],
        ),
    ]
    items = IntelligencePipeline().process(raw)
    expected_sources = 2
    assert len(items) == 1
    assert items[0].cross_source_confirmation_count == expected_sources
    assert "BTC" in items[0].asset_tags
    assert items[0].credibility_score > Decimal("0.7")
