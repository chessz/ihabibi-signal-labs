"""Unit tests for market domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from signals_lab.domain.market import AssetPair, MarketObservation


@pytest.mark.unit
def test_asset_pair_normalized_symbol() -> None:
    pair = AssetPair(
        symbol="BTC/USDT",
        base="BTC",
        quote="USDT",
        exchange="binance",
    )
    assert pair.normalized_symbol == "BINANCE:BTC_USDT"


@pytest.mark.unit
def test_market_observation_mid_price() -> None:
    pair = AssetPair(symbol="ETH/USDT", base="ETH", quote="USDT", exchange="binance")
    obs = MarketObservation(
        asset_pair=pair,
        timestamp=datetime.now(UTC),
        open=Decimal("3000"),
        high=Decimal("3100"),
        low=Decimal("2900"),
        close=Decimal("3050"),
        volume=Decimal("500"),
        source="test",
    )
    assert obs.mid_price == Decimal("3000")
