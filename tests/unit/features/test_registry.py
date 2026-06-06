"""Unit tests for FeatureRegistry."""

from __future__ import annotations

import pytest

from signals_lab.domain.enums import FeatureFamily
from signals_lab.domain.features import FeatureDefinition
from signals_lab.features.registry import FeatureRegistry


@pytest.mark.unit
def test_registry_loads_default_definitions() -> None:
    registry = FeatureRegistry()
    definitions = registry.list_enabled()
    names = {d.name for d in definitions}
    assert "sma_20" in names
    assert "rsi_14" in names
    assert "atr_14" in names


@pytest.mark.unit
def test_registry_get_compute_function() -> None:
    registry = FeatureRegistry()
    fn = registry.get_compute_function("sma")
    assert fn is not None
    assert fn.__name__ == "compute_sma"


@pytest.mark.unit
def test_registry_resolve_dependencies() -> None:
    parent = FeatureDefinition(
        name="parent",
        family=FeatureFamily.TREND,
        computation_function="sma",
        input_columns=["close"],
        dependencies=["child"],
    )
    child = FeatureDefinition(
        name="child",
        family=FeatureFamily.TREND,
        computation_function="sma",
        input_columns=["close"],
    )
    registry = FeatureRegistry(definitions=[parent, child])
    ordered = registry.resolve_dependencies("parent")
    assert [d.name for d in ordered] == ["child", "parent"]
