"""Feature engine — orchestrates feature computation with no-look-ahead enforcement."""

from __future__ import annotations

import time
import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

import structlog

from signals_lab.config import FeatureSettings, get_settings
from signals_lab.domain.features import FeatureBatch, FeatureDefinition, FeatureVector
from signals_lab.domain.market import AssetPair, MarketObservation

from .registry import FeatureRegistry

logger = structlog.get_logger(__name__)


class FeatureEngine:
    """Computes feature vectors from observations at a given point in time."""

    def __init__(
        self,
        registry: FeatureRegistry | None = None,
        settings: FeatureSettings | None = None,
    ) -> None:
        self._settings = settings or get_settings().features
        self._registry = registry or FeatureRegistry(settings=self._settings)

    @property
    def registry(self) -> FeatureRegistry:
        return self._registry

    def filter_observations(
        self,
        observations: Sequence[MarketObservation],
        as_of: datetime,
    ) -> list[MarketObservation]:
        """Keep only observations with timestamp <= as_of (no look-ahead)."""
        filtered = [obs for obs in observations if obs.timestamp <= as_of]
        if len(filtered) > self._settings.lookback_periods:
            filtered = filtered[-self._settings.lookback_periods :]
        return filtered

    def compute_single(
        self,
        definition: FeatureDefinition,
        observations: Sequence[MarketObservation],
        asset_pair: AssetPair,
        as_of: datetime,
        window: str,
    ) -> FeatureVector | None:
        """Compute one feature; returns None if insufficient data or NaN result."""
        if len(observations) < max(definition.min_data_points, self._settings.min_data_points):
            return None

        compute_fn = self._registry.get_compute_function(definition.computation_function)
        if compute_fn is None:
            logger.warning(
                "unknown_computation_function",
                function=definition.computation_function,
                feature=definition.name,
            )
            return None

        try:
            value: Decimal = compute_fn(observations, definition.params)
        except NotImplementedError:
            logger.debug("feature_not_implemented", feature=definition.name)
            return None
        except Exception:
            logger.exception("feature_computation_failed", feature=definition.name)
            return None

        if value.is_nan():
            return None

        return FeatureVector(
            asset_pair=asset_pair,
            timestamp=as_of,
            feature_family=definition.family,
            feature_name=definition.name,
            value=value,
            window=window,
            computation_version=definition.version,
        )

    def compute_batch(
        self,
        observations: Sequence[MarketObservation],
        asset_pair: AssetPair,
        as_of: datetime,
        window: str = "1d",
    ) -> FeatureBatch:
        """Compute all enabled features for an asset at ``as_of``."""
        start_ms = time.perf_counter()
        batch_id = str(uuid.uuid4())
        filtered = self.filter_observations(observations, as_of)
        features: list[FeatureVector] = []
        errors: list[dict[str, Any]] = []

        for definition in self._registry.list_enabled():
            vector = self.compute_single(definition, filtered, asset_pair, as_of, window)
            if vector is not None:
                features.append(vector)
            elif len(filtered) < self._settings.min_data_points:
                errors.append(
                    {
                        "feature": definition.name,
                        "error": "insufficient_data",
                        "available": len(filtered),
                        "required": self._settings.min_data_points,
                    }
                )

        elapsed_ms = int((time.perf_counter() - start_ms) * 1000)
        valid_from = filtered[0].timestamp if filtered else as_of
        valid_to = as_of

        return FeatureBatch(
            batch_id=batch_id,
            computed_at=datetime.utcnow(),
            features=features,
            asset_pairs=[asset_pair.normalized_symbol],
            windows=[window],
            valid_from=valid_from,
            valid_to=valid_to,
            computation_time_ms=elapsed_ms,
            errors=errors,
        )
