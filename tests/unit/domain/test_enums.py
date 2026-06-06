"""Unit tests for domain enums."""

from __future__ import annotations

import pytest

from signals_lab.domain.enums import ConfidenceBand, SignalClass


@pytest.mark.unit
class TestConfidenceBand:
    def test_all_bands_exist(self) -> None:
        assert ConfidenceBand.LOW.value == "low"
        assert ConfidenceBand.MEDIUM.value == "medium"
        assert ConfidenceBand.HIGH.value == "high"
        assert ConfidenceBand.EXTREME.value == "extreme"


@pytest.mark.unit
class TestSignalClass:
    def test_long_candidate_value(self) -> None:
        assert SignalClass.LONG_CANDIDATE.value == "long_candidate"

    def test_signal_class_is_str_enum(self) -> None:
        assert isinstance(SignalClass.LONG_CANDIDATE, str)
