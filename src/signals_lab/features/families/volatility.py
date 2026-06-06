"""Volatility feature family — ATR and realized volatility."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from signals_lab.domain.market import MarketObservation

from .common import extract_closes, extract_highs, extract_lows, has_enough_data


def compute_atr(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    period = int(params.get("period", 14))
    if not has_enough_data(observations, period + 1):
        return Decimal("NaN")

    tr_values: list[Decimal] = []
    highs = extract_highs(observations)
    lows = extract_lows(observations)
    closes = extract_closes(observations)
    for idx in range(1, len(observations)):
        tr = max(
            highs[idx] - lows[idx],
            abs(highs[idx] - closes[idx - 1]),
            abs(lows[idx] - closes[idx - 1]),
        )
        tr_values.append(tr)
    return sum(tr_values[-period:]) / Decimal(period)


def compute_realized_vol(
    observations: Sequence[MarketObservation],
    params: dict[str, Any],
) -> Decimal:
    """Annualized realized volatility from log returns."""
    period = int(params.get("period", 20))
    annualization = Decimal(str(params.get("annualization", 365)))
    closes = extract_closes(observations)
    if not has_enough_data(closes, period + 1):
        return Decimal("NaN")

    returns: list[Decimal] = []
    window = closes[-(period + 1) :]
    for idx in range(1, len(window)):
        if window[idx - 1] == 0:
            continue
        ratio = window[idx] / window[idx - 1]
        returns.append(ratio.ln())

    if len(returns) < 2:  # noqa: PLR2004
        return Decimal("NaN")

    mean = sum(returns) / Decimal(len(returns))
    variance = sum((ret - mean) ** 2 for ret in returns) / Decimal(len(returns) - 1)
    return variance.sqrt() * annualization.sqrt()


VOLATILITY_FUNCTIONS = {
    "atr": compute_atr,
    "realized_vol": compute_realized_vol,
}
