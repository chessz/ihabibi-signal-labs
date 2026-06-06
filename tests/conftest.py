"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from signals_lab.domain.enums import FeatureFamily, SignalClass
from signals_lab.domain.features import FeatureVector
from signals_lab.domain.market import AssetPair, MarketObservation
from signals_lab.domain.signals import SignalRule


@pytest.fixture
def btc_pair() -> AssetPair:
    return AssetPair(
        symbol="BTC/USDT",
        base="BTC",
        quote="USDT",
        exchange="binance",
    )


@pytest.fixture
def sample_observations(btc_pair: AssetPair) -> list[MarketObservation]:
    """60 synthetic OHLCV bars with a gentle uptrend."""
    base_time = datetime(2024, 1, 1, tzinfo=UTC)
    observations: list[MarketObservation] = []
    price = Decimal("40000")
    for idx in range(60):
        delta = Decimal(str(idx * 10))
        close = price + delta
        observations.append(
            MarketObservation(
                asset_pair=btc_pair,
                timestamp=base_time + timedelta(hours=idx),
                open=close - Decimal("50"),
                high=close + Decimal("100"),
                low=close - Decimal("100"),
                close=close,
                volume=Decimal("1000"),
                source="test",
            )
        )
    return observations


@pytest.fixture
def rsi_feature(btc_pair: AssetPair) -> FeatureVector:
    return FeatureVector(
        asset_pair=btc_pair,
        timestamp=datetime(2024, 1, 3, tzinfo=UTC),
        feature_family=FeatureFamily.MOMENTUM,
        feature_name="rsi_14",
        value=Decimal("65"),
        window="1d",
    )


@pytest.fixture
def macd_feature(btc_pair: AssetPair) -> FeatureVector:
    return FeatureVector(
        asset_pair=btc_pair,
        timestamp=datetime(2024, 1, 3, tzinfo=UTC),
        feature_family=FeatureFamily.MOMENTUM,
        feature_name="macd_histogram",
        value=Decimal("150"),
        window="1d",
    )


@pytest.fixture
def long_momentum_rule() -> SignalRule:
    return SignalRule(
        rule_id="long_momentum_v1",
        name="Long Momentum",
        description="RSI above 55 with positive MACD histogram",
        version="1.0.0",
        signal_class=SignalClass.LONG_CANDIDATE,
        conditions={
            "all": [
                {"feature": "rsi_14", "operator": "gte", "threshold": 55},
                {"feature": "macd_histogram", "operator": "gt", "threshold": 0},
            ]
        },
        required_features=["rsi_14", "macd_histogram"],
        min_confidence=Decimal("60"),
        cooldown_hours=4,
    )
