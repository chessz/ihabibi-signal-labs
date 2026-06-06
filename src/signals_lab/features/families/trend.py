"""Trend feature family — moving averages and trend strength."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from signals_lab.domain.market import MarketObservation

from .common import ema, extract_closes, extract_highs, extract_lows, has_enough_data, sma


def compute_sma(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    period = int(params["period"])
    closes = extract_closes(observations)
    return sma(closes, period)


def compute_ema(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    period = int(params["period"])
    closes = extract_closes(observations)
    return ema(closes, period)


def compute_adx(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    """Simplified ADX(period) using Wilder smoothing."""
    period = int(params.get("period", 14))
    if not has_enough_data(observations, period + 1):
        return Decimal("NaN")

    highs = extract_highs(observations)
    lows = extract_lows(observations)
    closes = extract_closes(observations)

    plus_dm: list[Decimal] = []
    minus_dm: list[Decimal] = []
    tr_values: list[Decimal] = []

    for idx in range(1, len(observations)):
        up_move = highs[idx] - highs[idx - 1]
        down_move = lows[idx - 1] - lows[idx]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else Decimal("0"))
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else Decimal("0"))
        tr = max(
            highs[idx] - lows[idx],
            abs(highs[idx] - closes[idx - 1]),
            abs(lows[idx] - closes[idx - 1]),
        )
        tr_values.append(tr)

    if len(tr_values) < period:
        return Decimal("NaN")

    atr = sum(tr_values[-period:]) / Decimal(period)
    if atr == 0:
        return Decimal("0")

    plus_di = (sum(plus_dm[-period:]) / Decimal(period)) / atr * Decimal("100")
    minus_di = (sum(minus_dm[-period:]) / Decimal(period)) / atr * Decimal("100")
    di_sum = plus_di + minus_di
    if di_sum == 0:
        return Decimal("0")
    dx = abs(plus_di - minus_di) / di_sum * Decimal("100")
    return dx


TREND_FUNCTIONS = {
    "sma": compute_sma,
    "ema": compute_ema,
    "adx": compute_adx,
}
