"""Rule engine — evaluates signal rules against feature vectors."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import structlog

from signals_lab.domain.enums import MarketRegime, SignalClass, SignalSide
from signals_lab.domain.features import FeatureVector
from signals_lab.domain.market import AssetPair
from signals_lab.domain.signals import ContributingFactor, SignalCandidate, SignalRule

logger = structlog.get_logger(__name__)

# Supported predicate operators in conditions tree
_OPERATORS = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
}


class RuleEngine:
    """Evaluates configurable signal rules against computed features."""

    def __init__(self, rules: list[SignalRule] | None = None) -> None:
        self._rules: list[SignalRule] = rules or []
        self._last_fired: dict[str, datetime] = {}

    def load_rules(self, rules: list[SignalRule]) -> None:
        self._rules = [r for r in rules if r.enabled]

    def evaluate(
        self,
        features: list[FeatureVector],
        asset_pair: AssetPair,
        regime: MarketRegime = MarketRegime.UNKNOWN,
        as_of: datetime | None = None,
    ) -> list[SignalCandidate]:
        """Evaluate all rules; return matching candidates."""
        as_of = as_of or datetime.utcnow()
        feature_map = {f.feature_name: f for f in features}
        candidates: list[SignalCandidate] = []

        for rule in self._rules:
            if not self._has_required_features(rule, feature_map):
                continue
            if not self._cooldown_elapsed(rule, asset_pair, as_of):
                continue
            if not self._regime_allowed(rule, regime):
                continue
            if not self._evaluate_conditions(rule.conditions, feature_map):
                continue

            raw_score, factors = self._compute_score(rule, feature_map)
            if raw_score < rule.min_confidence:
                continue

            side = self._signal_side(rule.signal_class)
            candidate = SignalCandidate(
                asset_pair=asset_pair,
                rule_id=rule.rule_id,
                signal_class=rule.signal_class,
                side=side,
                raw_score=raw_score,
                contributing_factors=factors,
                regime=regime,
                thesis_template=rule.description,
                generated_at=as_of,
            )
            candidates.append(candidate)
            self._last_fired[self._cooldown_key(rule, asset_pair)] = as_of

        return candidates

    def _evaluate_conditions(
        self,
        conditions: dict[str, Any],
        feature_map: dict[str, FeatureVector],
    ) -> bool:
        """Evaluate a predicate tree. Empty conditions pass by default."""
        if not conditions:
            return True

        if "all" in conditions:
            return all(
                self._evaluate_leaf(leaf, feature_map) for leaf in conditions["all"]
            )
        if "any" in conditions:
            return any(
                self._evaluate_leaf(leaf, feature_map) for leaf in conditions["any"]
            )
        if "not" in conditions:
            return not self._evaluate_conditions(conditions["not"], feature_map)

        return self._evaluate_leaf(conditions, feature_map)

    def _evaluate_leaf(
        self,
        leaf: dict[str, Any],
        feature_map: dict[str, FeatureVector],
    ) -> bool:
        feature_name = leaf.get("feature")
        if feature_name is None:
            return False
        vector = feature_map.get(feature_name)
        if vector is None:
            return False

        operator = leaf.get("operator", "gte")
        threshold = Decimal(str(leaf.get("threshold", 0)))
        op_fn = _OPERATORS.get(operator)
        if op_fn is None:
            logger.warning("unknown_operator", operator=operator)
            return False
        return bool(op_fn(vector.value, threshold))

    def _compute_score(
        self,
        rule: SignalRule,
        feature_map: dict[str, FeatureVector],
    ) -> tuple[Decimal, list[ContributingFactor]]:
        factors: list[ContributingFactor] = []
        total_weight = Decimal("0")
        weighted_sum = Decimal("0")

        for feature_name in rule.required_features:
            vector = feature_map.get(feature_name)
            if vector is None:
                continue
            weight = Decimal("1") / Decimal(len(rule.required_features))
            direction = self._infer_direction(vector.value, feature_name)
            factor = ContributingFactor(
                feature_family=vector.feature_family.value,
                feature_name=feature_name,
                value=vector.value,
                weight=weight,
                direction=direction,
                description=f"{feature_name}={vector.value}",
            )
            factors.append(factor)
            feature_score = self._feature_to_score(vector.value, feature_name)
            weighted_sum += feature_score * weight
            total_weight += weight

        if total_weight == 0:
            return Decimal("0"), factors

        raw_score = (weighted_sum / total_weight) * rule.weight
        raw_score = max(Decimal("0"), min(Decimal("100"), raw_score))
        return raw_score, factors

    def _feature_to_score(self, value: Decimal, feature_name: str) -> Decimal:
        """Map a feature value to a 0-100 contribution score."""
        name_lower = feature_name.lower()
        if "rsi" in name_lower:
            return value
        if "macd" in name_lower:
            return Decimal("50") + min(Decimal("50"), max(Decimal("-50"), value))
        if "zscore" in name_lower:
            return Decimal("50") + min(Decimal("50"), max(Decimal("-50"), value * Decimal("10")))
        if "bb_pct" in name_lower or "stochastic" in name_lower:
            return value * Decimal("100") if value <= Decimal("1") else value
        if "adx" in name_lower:
            return min(Decimal("100"), value)
        return Decimal("50")

    def _infer_direction(self, value: Decimal, feature_name: str) -> str:
        name_lower = feature_name.lower()
        if "rsi" in name_lower:
            if value >= Decimal("55"):
                return "bullish"
            if value <= Decimal("45"):
                return "bearish"
        if "macd" in name_lower:
            if value > 0:
                return "bullish"
            if value < 0:
                return "bearish"
        return "neutral"

    def _has_required_features(
        self,
        rule: SignalRule,
        feature_map: dict[str, FeatureVector],
    ) -> bool:
        if not rule.required_features:
            return True
        return all(name in feature_map for name in rule.required_features)

    def _cooldown_elapsed(
        self,
        rule: SignalRule,
        asset_pair: AssetPair,
        as_of: datetime,
    ) -> bool:
        key = self._cooldown_key(rule, asset_pair)
        last = self._last_fired.get(key)
        if last is None:
            return True
        return as_of - last >= timedelta(hours=rule.cooldown_hours)

    @staticmethod
    def _cooldown_key(rule: SignalRule, asset_pair: AssetPair) -> str:
        return f"{rule.rule_id}:{asset_pair.normalized_symbol}"

    def _regime_allowed(self, rule: SignalRule, regime: MarketRegime) -> bool:
        if regime in (MarketRegime.VOLATILE, MarketRegime.UNKNOWN):
            return bool(rule.signal_class == SignalClass.WATCH_ONLY)
        if rule.signal_class == SignalClass.LONG_CANDIDATE:
            return regime in (MarketRegime.TRENDING_UP, MarketRegime.RANGING, MarketRegime.UNKNOWN)
        if rule.signal_class == SignalClass.SHORT_CANDIDATE:
            return regime in (MarketRegime.TRENDING_DOWN, MarketRegime.RANGING, MarketRegime.UNKNOWN)
        return True

    @staticmethod
    def _signal_side(signal_class: SignalClass) -> SignalSide:
        if signal_class == SignalClass.LONG_CANDIDATE:
            return SignalSide.BUY
        if signal_class == SignalClass.SHORT_CANDIDATE:
            return SignalSide.SELL
        return SignalSide.NEUTRAL
