"""Unit tests for asset tag extraction."""

from __future__ import annotations

import pytest

from signals_lab.ingestion.normalizer import extract_asset_tags


@pytest.mark.unit
def test_extract_asset_tags_from_text() -> None:
    tags = extract_asset_tags("Bitcoin and Ethereum rally as Solana gains")
    assert "BTC" in tags
    assert "ETH" in tags
    assert "SOL" in tags


@pytest.mark.unit
def test_extract_asset_tags_respects_hints() -> None:
    tags = extract_asset_tags("Market update", hints=["AVAX"])
    assert tags == ["AVAX"]
