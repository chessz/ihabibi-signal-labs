"""Confidence calibration — maps raw scores to bands."""

from __future__ import annotations

from decimal import Decimal

from signals_lab.config import SignalSettings, get_settings
from signals_lab.domain.enums import ConfidenceBand


class ConfidenceCalibrator:
    """Maps a raw score in [0, 100] to confidence_score and confidence_band."""

    def __init__(self, settings: SignalSettings | None = None) -> None:
        self._settings = settings or get_settings().signals

    def calibrate(self, raw_score: Decimal) -> tuple[Decimal, ConfidenceBand]:
        """Return (confidence_score, confidence_band) for a raw score."""
        score = max(Decimal("0"), min(Decimal("100"), raw_score))
        band = self._score_to_band(score)
        return score, band

    def is_publishable(self, band: ConfidenceBand) -> bool:
        return band in (ConfidenceBand.HIGH, ConfidenceBand.EXTREME)

    def meets_publish_threshold(self, score: Decimal) -> bool:
        return score >= Decimal(str(self._settings.min_confidence_for_publish))

    def _score_to_band(self, score: Decimal) -> ConfidenceBand:
        bands = self._settings.confidence_bands
        for band_name in ("low", "medium", "high", "extreme"):
            bounds = bands.get(band_name)
            if bounds is None or len(bounds) < 2:  # noqa: PLR2004
                continue
            low, high = Decimal(str(bounds[0])), Decimal(str(bounds[1]))
            if band_name == "extreme":
                if low <= score <= high:
                    return ConfidenceBand(band_name)
            elif low <= score < high:
                return ConfidenceBand(band_name)
        return ConfidenceBand.LOW
