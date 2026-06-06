"""Unit tests for Signal domain model."""

from __future__ import annotations

from decimal import Decimal

import pytest

from signals_lab.domain.enums import ConfidenceBand, SignalClass, SignalSide, SignalStatus
from signals_lab.domain.market import AssetPair
from signals_lab.domain.signals import Signal


@pytest.fixture
def btc_pair() -> AssetPair:
    return AssetPair(
        symbol="BTC/USDT",
        base="BTC",
        quote="USDT",
        exchange="binance",
    )


@pytest.mark.unit
def test_signal_is_publishable_only_for_high_extreme(btc_pair: AssetPair) -> None:
    for band, expected in [
        (ConfidenceBand.LOW, False),
        (ConfidenceBand.MEDIUM, False),
        (ConfidenceBand.HIGH, True),
        (ConfidenceBand.EXTREME, True),
    ]:
        sig = Signal(
            asset_pair=btc_pair,
            signal_class=SignalClass.LONG_CANDIDATE,
            side=SignalSide.BUY,
            confidence_score=Decimal("75"),
            confidence_band=band,
            thesis="Momentum + trend alignment, RSI 60, MACD bullish cross.",
            invalidation_condition="4h close below 50EMA",
        )
        assert sig.is_publishable is expected


@pytest.mark.unit
def test_signal_is_active_when_status_active(btc_pair: AssetPair) -> None:
    sig = Signal(
        asset_pair=btc_pair,
        signal_class=SignalClass.LONG_CANDIDATE,
        side=SignalSide.BUY,
        confidence_score=Decimal("75"),
        confidence_band=ConfidenceBand.HIGH,
        thesis="Momentum + trend alignment, RSI 60, MACD bullish cross.",
        invalidation_condition="4h close below 50EMA",
        status=SignalStatus.ACTIVE,
    )
    assert sig.is_active is True
