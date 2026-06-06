"""Social feature family — stub until API keys and data pipelines are ready."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from signals_lab.domain.social import SocialObservation


def compute_mention_velocity(
    observations: Sequence[SocialObservation],
    params: dict[str, Any],
) -> Decimal:
    raise NotImplementedError("Social features require LunarCrush ingestion (Stage 2.5)")


def compute_sentiment_divergence(
    observations: Sequence[SocialObservation],
    params: dict[str, Any],
) -> Decimal:
    raise NotImplementedError("Social features require LunarCrush ingestion (Stage 2.5)")


SOCIAL_FUNCTIONS = {
    "mention_velocity": compute_mention_velocity,
    "sentiment_divergence": compute_sentiment_divergence,
}
