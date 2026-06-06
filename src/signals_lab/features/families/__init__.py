"""Feature family modules."""

from __future__ import annotations

from .events import EVENTS_FUNCTIONS
from .mean_reversion import MEAN_REVERSION_FUNCTIONS
from .momentum import MOMENTUM_FUNCTIONS
from .onchain import ONCHAIN_FUNCTIONS
from .social import SOCIAL_FUNCTIONS
from .trend import TREND_FUNCTIONS
from .volatility import VOLATILITY_FUNCTIONS

ALL_COMPUTE_FUNCTIONS = {
    **TREND_FUNCTIONS,
    **MOMENTUM_FUNCTIONS,
    **MEAN_REVERSION_FUNCTIONS,
    **VOLATILITY_FUNCTIONS,
    **SOCIAL_FUNCTIONS,
    **ONCHAIN_FUNCTIONS,
    **EVENTS_FUNCTIONS,
}

__all__ = [
    "ALL_COMPUTE_FUNCTIONS",
    "TREND_FUNCTIONS",
    "MOMENTUM_FUNCTIONS",
    "MEAN_REVERSION_FUNCTIONS",
    "VOLATILITY_FUNCTIONS",
    "SOCIAL_FUNCTIONS",
    "ONCHAIN_FUNCTIONS",
    "EVENTS_FUNCTIONS",
]
