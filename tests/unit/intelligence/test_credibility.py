"""Unit tests for credibility scoring."""

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
from signals_lab.intelligence.credibility import apply_credibility_penalties, score_credibility


def _item(title: str, role: ContentRole, cred: str = "0.7") -> IntelligenceItem:
    return IntelligenceItem(
        external_id="x:1",
        dedup_key="k1",
        observed_at=datetime(2026, 6, 6, 12, 0, 0),
        provider="rss_fan_in",
        provider_tier=ProviderTier.A,
        source_type=IntelligenceSourceType.NEWS,
        original_source="Test",
        content_role=role,
        title=title,
        credibility_score=Decimal(cred),
    )


@pytest.mark.unit
def test_rumor_penalized_vs_primary() -> None:
    primary = score_credibility(_item("ETF approved", ContentRole.PRIMARY))
    rumor = score_credibility(_item("ETF approved", ContentRole.RUMOR))
    assert primary > rumor


@pytest.mark.unit
def test_clickbait_penalty() -> None:
    item = _item("You won't believe this SHOCKING crypto move!!!", ContentRole.PRIMARY)
    penalized = apply_credibility_penalties(item)
    assert penalized.credibility_score < item.credibility_score


@pytest.mark.unit
def test_confirmation_boost() -> None:
    item = _item("Bitcoin rally continues", ContentRole.PRIMARY).model_copy(
        update={"cross_source_confirmation_count": 3, "confirming_providers": ["a", "b", "c"]}
    )
    boosted = score_credibility(item)
    base = score_credibility(item.model_copy(update={"cross_source_confirmation_count": 1}))
    assert boosted > base
