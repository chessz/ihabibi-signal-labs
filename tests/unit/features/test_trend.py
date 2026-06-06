"""Unit tests for trend feature computations."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from signals_lab.domain.market import AssetPair, MarketObservation
from signals_lab.features.families.trend import compute_ema, compute_sma


@pytest.mark.unit
def test_sma_known_values() -> None:
    closes = [Decimal(str(i)) for i in range(1, 21)]
    result = compute_sma(
        [_make_obs(c) for c in closes],
        {"period": 20},
    )
    assert result == Decimal("10.5")


@pytest.mark.unit
def test_sma_insufficient_data() -> None:
    closes = [Decimal("1"), Decimal("2")]
    result = compute_sma([_make_obs(c) for c in closes], {"period": 20})
    assert result.is_nan()


@pytest.mark.unit
def test_ema_returns_value_with_enough_data() -> None:
    closes = [Decimal(str(100 + i)) for i in range(30)]
    result = compute_ema([_make_obs(c) for c in closes], {"period": 12})
    assert not result.is_nan()
    assert result > Decimal("100")


def _make_obs(close: Decimal) -> MarketObservation:
    pair = AssetPair(symbol="BTC/USDT", base="BTC", quote="USDT", exchange="binance")
    return MarketObservation(
        asset_pair=pair,
        timestamp=datetime.now(UTC),
        open=close,
        high=close + Decimal("1"),
        low=close - Decimal("1"),
        close=close,
        volume=Decimal("100"),
        source="test",
    )
