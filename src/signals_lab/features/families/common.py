"""Shared helpers for feature family computations."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TypeVar

T = TypeVar("T")


def filter_no_look_ahead(
    observations: Sequence[T],
    as_of_times: Sequence[object],
    as_of: object,
) -> list[T]:
    """Return observations whose timestamp is at or before ``as_of``."""
    return [
        obs
        for obs, ts in zip(observations, as_of_times, strict=True)
        if ts <= as_of  # type: ignore[operator]
    ]


def extract_closes(observations: Sequence[object]) -> list[Decimal]:
    """Extract close prices from market observations."""
    return [obs.close for obs in observations]  # type: ignore[attr-defined]


def extract_highs(observations: Sequence[object]) -> list[Decimal]:
    return [obs.high for obs in observations]  # type: ignore[attr-defined]


def extract_lows(observations: Sequence[object]) -> list[Decimal]:
    return [obs.low for obs in observations]  # type: ignore[attr-defined]


def insufficient_data() -> Decimal:
    return Decimal("NaN")


def has_enough_data(values: Sequence[object], period: int) -> bool:
    return len(values) >= period


def sma(values: Sequence[Decimal], period: int) -> Decimal:
    if not has_enough_data(values, period):
        return insufficient_data()
    window = values[-period:]
    return sum(window) / Decimal(period)


def ema(values: Sequence[Decimal], period: int) -> Decimal:
    if not has_enough_data(values, period):
        return insufficient_data()
    multiplier = Decimal(2) / Decimal(period + 1)
    ema_value = sum(values[:period]) / Decimal(period)
    for price in values[period:]:
        ema_value = (price - ema_value) * multiplier + ema_value
    return ema_value
