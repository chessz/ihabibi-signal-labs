"""Unit tests for ConfidenceCalibrator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from signals_lab.domain.enums import ConfidenceBand
from signals_lab.signals.confidence import ConfidenceCalibrator


@pytest.mark.unit
class TestConfidenceCalibrator:
    def test_low_band(self) -> None:
        calibrator = ConfidenceCalibrator()
        score, band = calibrator.calibrate(Decimal("25"))
        assert band == ConfidenceBand.LOW
        assert score == Decimal("25")

    def test_medium_band(self) -> None:
        calibrator = ConfidenceCalibrator()
        _, band = calibrator.calibrate(Decimal("50"))
        assert band == ConfidenceBand.MEDIUM

    def test_high_band(self) -> None:
        calibrator = ConfidenceCalibrator()
        _, band = calibrator.calibrate(Decimal("70"))
        assert band == ConfidenceBand.HIGH

    def test_extreme_band(self) -> None:
        calibrator = ConfidenceCalibrator()
        _, band = calibrator.calibrate(Decimal("90"))
        assert band == ConfidenceBand.EXTREME

    def test_clamps_out_of_range(self) -> None:
        calibrator = ConfidenceCalibrator()
        score, _ = calibrator.calibrate(Decimal("150"))
        assert score == Decimal("100")

    def test_is_publishable(self) -> None:
        calibrator = ConfidenceCalibrator()
        assert calibrator.is_publishable(ConfidenceBand.HIGH) is True
        assert calibrator.is_publishable(ConfidenceBand.LOW) is False

    def test_meets_publish_threshold(self) -> None:
        calibrator = ConfidenceCalibrator()
        assert calibrator.meets_publish_threshold(Decimal("75")) is True
        assert calibrator.meets_publish_threshold(Decimal("50")) is False
