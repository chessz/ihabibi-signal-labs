"""Unit tests for intelligence API routes."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from signals_lab.api.app import create_app
from signals_lab.api.services.seed_intelligence import ID_BTC_STRATEGY

SIGNAL_BTC = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
_HTTP_OK = 200


@pytest.fixture
def app():
    return create_app()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_healthz(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == _HTTP_OK
    assert response.json()["status"] == "ok"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_intelligence_ticker_returns_items(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/intelligence/ticker?limit=5")
    assert response.status_code == _HTTP_OK
    body = response.json()
    assert len(body["items"]) >= 1
    assert "title" in body["items"][0]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_signal_includes_linked_intelligence(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/signals/{SIGNAL_BTC}")
    assert response.status_code == _HTTP_OK
    body = response.json()
    assert len(body["linked_intelligence"]) >= 1
    intel_ids = {item["intelligence_id"] for item in body["linked_intelligence"]}
    assert str(ID_BTC_STRATEGY) in intel_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_intelligence_item_signals_reverse_lookup(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/intelligence/{ID_BTC_STRATEGY}/signals")
    assert response.status_code == _HTTP_OK
    body = response.json()
    assert str(SIGNAL_BTC) in {str(s) for s in body["signal_ids"]}
