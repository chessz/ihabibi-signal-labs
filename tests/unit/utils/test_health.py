"""Unit tests for health check utilities."""

from __future__ import annotations

import pytest

from signals_lab.utils.health import (
    HealthCheckResult,
    HealthStatus,
    format_results,
    summarize_results,
)


@pytest.mark.unit
def test_summarize_results() -> None:
    results = [
        HealthCheckResult("a", "api", HealthStatus.OK, "ok"),
        HealthCheckResult("b", "api", HealthStatus.WARN, "warn"),
        HealthCheckResult("c", "db", HealthStatus.FAIL, "fail"),
        HealthCheckResult("d", "db", HealthStatus.SKIP, "skip"),
    ]
    assert summarize_results(results) == (1, 1, 1, 1)


@pytest.mark.unit
def test_format_results_includes_status_and_name() -> None:
    text = format_results(
        [HealthCheckResult("binance", "api", HealthStatus.OK, "ping OK", 42)]
    )
    assert "ok" in text
    assert "binance" in text
    assert "42ms" in text
