"""Events feature family — stub until event scoring is implemented."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from signals_lab.domain.events import EventObservation


def compute_event_risk_penalty(
    observations: Sequence[EventObservation],
    params: dict[str, Any],
) -> Decimal:
    raise NotImplementedError("Event features require event scoring pipeline (Stage 2.5)")


EVENTS_FUNCTIONS = {
    "event_risk_penalty": compute_event_risk_penalty,
}
