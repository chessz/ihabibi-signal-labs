"""Unit tests for FeatureEngine — no-look-ahead enforcement."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from signals_lab.domain.market import AssetPair, MarketObservation
from signals_lab.features.engine import FeatureEngine


@pytest.mark.unit
def test_filter_observations_excludes_future_data(
    sample_observations: list[MarketObservation],
) -> None:
    engine = FeatureEngine()
    as_of = sample_observations[30].timestamp
    filtered = engine.filter_observations(sample_observations, as_of)
    assert all(obs.timestamp <= as_of for obs in filtered)
    assert len(filtered) == 31  # noqa: PLR2004 — index 30 inclusive


@pytest.mark.unit
def test_compute_batch_no_look_ahead(
    sample_observations: list[MarketObservation],
    btc_pair: AssetPair,
) -> None:
    engine = FeatureEngine()
    as_of = sample_observations[55].timestamp
    batch = engine.compute_batch(sample_observations, btc_pair, as_of, window="1h")
    assert len(batch.features) > 0
    assert batch.valid_to == as_of


@pytest.mark.unit
def test_insufficient_data_returns_empty_features(btc_pair: AssetPair) -> None:
    engine = FeatureEngine()
    base_time = datetime(2024, 1, 1, tzinfo=UTC)
    few_obs = [
        MarketObservation(
            asset_pair=btc_pair,
            timestamp=base_time,
            open=Decimal("40000"),
            high=Decimal("40100"),
            low=Decimal("39900"),
            close=Decimal("40050"),
            volume=Decimal("100"),
            source="test",
        )
    ]
    batch = engine.compute_batch(few_obs, btc_pair, base_time)
    assert len(batch.features) == 0
    assert len(batch.errors) > 0
