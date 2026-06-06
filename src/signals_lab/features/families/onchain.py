"""On-chain feature family — stub until Glassnode/Nansen keys are configured."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from signals_lab.domain.onchain import OnChainObservation


def compute_flow_imbalance(
    observations: Sequence[OnChainObservation],
    params: dict[str, Any],
) -> Decimal:
    raise NotImplementedError("On-chain features require Glassnode ingestion (Stage 2.5)")


ONCHAIN_FUNCTIONS = {
    "flow_imbalance": compute_flow_imbalance,
}
