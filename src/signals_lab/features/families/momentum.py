"""Momentum feature family — RSI, MACD, ROC, Stochastic."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from signals_lab.domain.market import MarketObservation

from .common import ema, extract_closes, extract_highs, extract_lows, has_enough_data


def compute_rsi(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    period = int(params.get("period", 14))
    closes = extract_closes(observations)
    if not has_enough_data(closes, period + 1):
        return Decimal("NaN")

    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for idx in range(len(closes) - period, len(closes)):
        change = closes[idx] - closes[idx - 1]
        gains.append(max(change, Decimal("0")))
        losses.append(max(-change, Decimal("0")))

    avg_gain = sum(gains) / Decimal(period)
    avg_loss = sum(losses) / Decimal(period)
    if avg_loss == 0:
        return Decimal("100")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def compute_macd(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    """Returns MACD histogram (MACD line minus signal line)."""
    fast = int(params.get("fast", 12))
    slow = int(params.get("slow", 26))
    signal = int(params.get("signal", 9))
    closes = extract_closes(observations)
    if not has_enough_data(closes, slow + signal):
        return Decimal("NaN")

    macd_line = ema(closes, fast) - ema(closes, slow)
    macd_series: list[Decimal] = []
    for end in range(slow, len(closes) + 1):
        window = closes[:end]
        macd_series.append(ema(window, fast) - ema(window, slow))

    signal_line = ema(macd_series, signal)
    if macd_line.is_nan() or signal_line.is_nan():
        return Decimal("NaN")
    return macd_line - signal_line


def compute_roc(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    period = int(params.get("period", 10))
    closes = extract_closes(observations)
    if not has_enough_data(closes, period + 1):
        return Decimal("NaN")
    prior = closes[-period - 1]
    if prior == 0:
        return Decimal("0")
    return ((closes[-1] - prior) / prior) * Decimal("100")


def compute_stochastic(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    """Returns %K (fast stochastic)."""
    k_period = int(params.get("k_period", 14))
    if not has_enough_data(observations, k_period):
        return Decimal("NaN")

    highs = extract_highs(observations)[-k_period:]
    lows = extract_lows(observations)[-k_period:]
    close = extract_closes(observations)[-1]
    highest = max(highs)
    lowest = min(lows)
    if highest == lowest:
        return Decimal("50")
    return ((close - lowest) / (highest - lowest)) * Decimal("100")


MOMENTUM_FUNCTIONS = {
    "rsi": compute_rsi,
    "macd": compute_macd,
    "roc": compute_roc,
    "stochastic": compute_stochastic,
}
