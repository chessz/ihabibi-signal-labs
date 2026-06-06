"""Unit tests for RuleEngine."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from signals_lab.domain.enums import FeatureFamily, MarketRegime, SignalClass
from signals_lab.domain.features import FeatureVector
from signals_lab.domain.market import AssetPair
from signals_lab.domain.signals import SignalRule
from signals_lab.signals.rules import RuleEngine


@pytest.mark.unit
def test_rule_fires_when_conditions_met(
    btc_pair: AssetPair,
    rsi_feature: FeatureVector,
    macd_feature: FeatureVector,
    long_momentum_rule: SignalRule,
) -> None:
    engine = RuleEngine(rules=[long_momentum_rule])
    candidates = engine.evaluate(
        [rsi_feature, macd_feature],
        btc_pair,
        regime=MarketRegime.TRENDING_UP,
        as_of=datetime(2024, 1, 3, tzinfo=UTC),
    )
    assert len(candidates) == 1
    assert candidates[0].signal_class == SignalClass.LONG_CANDIDATE
    assert candidates[0].raw_score >= Decimal("60")


@pytest.mark.unit
def test_rule_does_not_fire_when_conditions_unmet(
    btc_pair: AssetPair,
    macd_feature: FeatureVector,
    long_momentum_rule: SignalRule,
) -> None:
    low_rsi = FeatureVector(
        asset_pair=btc_pair,
        timestamp=datetime(2024, 1, 3, tzinfo=UTC),
        feature_family=FeatureFamily.MOMENTUM,
        feature_name="rsi_14",
        value=Decimal("40"),
        window="1d",
    )
    engine = RuleEngine(rules=[long_momentum_rule])
    candidates = engine.evaluate(
        [low_rsi, macd_feature],
        btc_pair,
        regime=MarketRegime.TRENDING_UP,
    )
    assert len(candidates) == 0


@pytest.mark.unit
def test_cooldown_prevents_duplicate_signals(
    btc_pair: AssetPair,
    rsi_feature: FeatureVector,
    macd_feature: FeatureVector,
    long_momentum_rule: SignalRule,
) -> None:
    engine = RuleEngine(rules=[long_momentum_rule])
    as_of = datetime(2024, 1, 3, tzinfo=UTC)
    first = engine.evaluate(
        [rsi_feature, macd_feature], btc_pair, MarketRegime.TRENDING_UP, as_of
    )
    second = engine.evaluate(
        [rsi_feature, macd_feature], btc_pair, MarketRegime.TRENDING_UP, as_of
    )
    assert len(first) == 1
    assert len(second) == 0
