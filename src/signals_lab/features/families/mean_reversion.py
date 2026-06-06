"""Mean-reversion feature family — Bollinger Bands, Z-score."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from signals_lab.domain.market import MarketObservation

from .common import extract_closes, has_enough_data, sma


def _std_dev(values: Sequence[Decimal], mean: Decimal) -> Decimal:
    if len(values) < 2:  # noqa: PLR2004
        return Decimal("0")
    variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
    return variance.sqrt()


def compute_bollinger_pct_b(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    """Percent-B: position of price within Bollinger Bands (0=lower, 1=upper)."""
    period = int(params.get("period", 20))
    std_dev_mult = Decimal(str(params.get("std_dev", 2)))
    closes = extract_closes(observations)
    if not has_enough_data(closes, period):
        return Decimal("NaN")

    window = closes[-period:]
    mean = sma(window, period)
    std = _std_dev(window, mean)
    if std == 0:
        return Decimal("0.5")
    upper = mean + std_dev_mult * std
    lower = mean - std_dev_mult * std
    close = closes[-1]
    return (close - lower) / (upper - lower)


def compute_zscore(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    period = int(params.get("period", 20))
    closes = extract_closes(observations)
    if not has_enough_data(closes, period):
        return Decimal("NaN")

    window = closes[-period:]
    mean = sma(window, period)
    std = _std_dev(window, mean)
    if std == 0:
        return Decimal("0")
    return (closes[-1] - mean) / std


MEAN_REVERSION_FUNCTIONS = {
    "bollinger_pct_b": compute_bollinger_pct_b,
    "zscore": compute_zscore,
}
