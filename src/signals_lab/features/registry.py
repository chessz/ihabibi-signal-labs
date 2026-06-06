"""Feature registry — manages feature definitions and dependency resolution."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from decimal import Decimal

import structlog

from signals_lab.config import FeatureSettings, get_settings
from signals_lab.domain.enums import FeatureFamily
from signals_lab.domain.features import FeatureDefinition

from .families import ALL_COMPUTE_FUNCTIONS

logger = structlog.get_logger(__name__)


def _build_default_definitions(settings: FeatureSettings) -> list[FeatureDefinition]:
    """Seed feature definitions from settings.yaml family params."""
    families = settings.families
    trend_params = families.trend.params
    momentum_params = families.momentum.params
    mr_params = families.mean_reversion.params
    vol_params = families.volatility.params

    definitions: list[FeatureDefinition] = []

    if families.trend.enabled:
        for period in trend_params.get("sma_periods", [20, 50, 200]):
            definitions.append(
                FeatureDefinition(
                    name=f"sma_{period}",
                    family=FeatureFamily.TREND,
                    description=f"Simple moving average ({period})",
                    computation_function="sma",
                    input_columns=["close"],
                    windows=settings.computation_windows,
                    params={"period": period},
                )
            )
        for period in trend_params.get("ema_periods", [12, 26, 50]):
            definitions.append(
                FeatureDefinition(
                    name=f"ema_{period}",
                    family=FeatureFamily.TREND,
                    description=f"Exponential moving average ({period})",
                    computation_function="ema",
                    input_columns=["close"],
                    windows=settings.computation_windows,
                    params={"period": period},
                )
            )
        definitions.append(
            FeatureDefinition(
                name="adx_14",
                family=FeatureFamily.TREND,
                description="Average Directional Index (14)",
                computation_function="adx",
                input_columns=["high", "low", "close"],
                windows=settings.computation_windows,
                params={"period": trend_params.get("adx_period", 14)},
            )
        )

    if families.momentum.enabled:
        rsi_period = momentum_params.get("rsi_period", 14)
        definitions.append(
            FeatureDefinition(
                name=f"rsi_{rsi_period}",
                family=FeatureFamily.MOMENTUM,
                description=f"Relative Strength Index ({rsi_period})",
                computation_function="rsi",
                input_columns=["close"],
                windows=settings.computation_windows,
                params={"period": rsi_period},
            )
        )
        definitions.append(
            FeatureDefinition(
                name="macd_histogram",
                family=FeatureFamily.MOMENTUM,
                description="MACD histogram",
                computation_function="macd",
                input_columns=["close"],
                windows=settings.computation_windows,
                params={
                    "fast": momentum_params.get("macd_fast", 12),
                    "slow": momentum_params.get("macd_slow", 26),
                    "signal": momentum_params.get("macd_signal", 9),
                },
            )
        )
        roc_period = momentum_params.get("roc_period", 10)
        definitions.append(
            FeatureDefinition(
                name=f"roc_{roc_period}",
                family=FeatureFamily.MOMENTUM,
                description=f"Rate of change ({roc_period})",
                computation_function="roc",
                input_columns=["close"],
                windows=settings.computation_windows,
                params={"period": roc_period},
            )
        )
        definitions.append(
            FeatureDefinition(
                name="stochastic_k",
                family=FeatureFamily.MOMENTUM,
                description="Stochastic %K",
                computation_function="stochastic",
                input_columns=["high", "low", "close"],
                windows=settings.computation_windows,
                params={
                    "k_period": momentum_params.get("stoch_k_period", 14),
                    "d_period": momentum_params.get("stoch_d_period", 3),
                },
            )
        )

    if families.mean_reversion.enabled:
        bb_period = mr_params.get("bb_period", 20)
        definitions.append(
            FeatureDefinition(
                name=f"bb_pct_b_{bb_period}",
                family=FeatureFamily.MEAN_REVERSION,
                description=f"Bollinger %B ({bb_period})",
                computation_function="bollinger_pct_b",
                input_columns=["close"],
                windows=settings.computation_windows,
                params={
                    "period": bb_period,
                    "std_dev": mr_params.get("bb_std_dev", 2),
                },
            )
        )
        zscore_period = mr_params.get("zscore_period", 20)
        definitions.append(
            FeatureDefinition(
                name=f"zscore_{zscore_period}",
                family=FeatureFamily.MEAN_REVERSION,
                description=f"Price Z-score ({zscore_period})",
                computation_function="zscore",
                input_columns=["close"],
                windows=settings.computation_windows,
                params={"period": zscore_period},
            )
        )

    if families.volatility.enabled:
        atr_period = vol_params.get("atr_period", 14)
        definitions.append(
            FeatureDefinition(
                name=f"atr_{atr_period}",
                family=FeatureFamily.VOLATILITY,
                description=f"Average True Range ({atr_period})",
                computation_function="atr",
                input_columns=["high", "low", "close"],
                windows=settings.computation_windows,
                params={"period": atr_period},
            )
        )
        rv_period = vol_params.get("realized_vol_period", 20)
        definitions.append(
            FeatureDefinition(
                name=f"realized_vol_{rv_period}",
                family=FeatureFamily.VOLATILITY,
                description=f"Realized volatility ({rv_period})",
                computation_function="realized_vol",
                input_columns=["close"],
                windows=settings.computation_windows,
                params={
                    "period": rv_period,
                    "annualization": vol_params.get("realized_vol_annualization", 365),
                },
            )
        )

    return definitions


class FeatureRegistry:
    """In-memory registry of feature definitions with dependency resolution."""

    def __init__(
        self,
        definitions: Iterable[FeatureDefinition] | None = None,
        settings: FeatureSettings | None = None,
    ) -> None:
        self._settings = settings or get_settings().features
        self._definitions: dict[str, FeatureDefinition] = {}
        if definitions is None:
            definitions = _build_default_definitions(self._settings)
        for definition in definitions:
            self.register(definition)

    def register(self, definition: FeatureDefinition) -> None:
        if not self._is_family_enabled(definition.family):
            logger.debug(
                "feature_family_disabled",
                feature=definition.name,
                family=definition.family.value,
            )
            return
        self._definitions[definition.name] = definition

    def get(self, name: str) -> FeatureDefinition | None:
        return self._definitions.get(name)

    def list_all(self) -> list[FeatureDefinition]:
        return list(self._definitions.values())

    def list_enabled(self) -> list[FeatureDefinition]:
        return [d for d in self._definitions.values() if d.enabled]

    def resolve_dependencies(self, name: str) -> list[FeatureDefinition]:
        """Return definitions in dependency order (dependencies first)."""
        ordered: list[FeatureDefinition] = []
        seen: set[str] = set()

        def visit(feature_name: str) -> None:
            if feature_name in seen:
                return
            definition = self._definitions.get(feature_name)
            if definition is None:
                return
            for dep in definition.dependencies:
                visit(dep)
            seen.add(feature_name)
            ordered.append(definition)

        visit(name)
        return ordered

    def get_compute_function(
        self, computation_function: str
    ) -> Callable[..., Decimal] | None:
        fn = ALL_COMPUTE_FUNCTIONS.get(computation_function)
        return fn  # type: ignore[return-value]

    def _is_family_enabled(self, family: FeatureFamily) -> bool:
        family_map: dict[FeatureFamily, bool] = {
            FeatureFamily.TREND: self._settings.families.trend.enabled,
            FeatureFamily.MOMENTUM: self._settings.families.momentum.enabled,
            FeatureFamily.MEAN_REVERSION: self._settings.families.mean_reversion.enabled,
            FeatureFamily.VOLATILITY: self._settings.families.volatility.enabled,
            FeatureFamily.SOCIAL: self._settings.families.social.enabled,
            FeatureFamily.ONCHAIN: self._settings.families.onchain.enabled,
            FeatureFamily.EVENTS: self._settings.families.events.enabled,
            FeatureFamily.CROSS_ASSET: self._settings.families.cross_asset.enabled,
        }
        return family_map.get(family, False)
