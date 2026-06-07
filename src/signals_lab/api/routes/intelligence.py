"""Intelligence feed and ticker routes."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from signals_lab.api.dependencies import get_intel_cache, get_signals
from signals_lab.api.schemas.intelligence import (
    IntelligenceFeedResponse,
    IntelligenceItemSchema,
    IntelligenceSignalsResponse,
    IntelligenceTickerResponse,
    intelligence_from_domain,
)
from signals_lab.api.services.intelligence_cache import IntelligenceCache
from signals_lab.api.services.signal_catalog import SignalCatalog

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/ticker", response_model=IntelligenceTickerResponse)
async def get_ticker(
    limit: int = Query(default=12, ge=1, le=50),
    cache: IntelligenceCache = Depends(get_intel_cache),
) -> IntelligenceTickerResponse:
    items = await cache.get_ticker(limit=limit)
    return IntelligenceTickerResponse(
        generated_at=datetime.utcnow(),
        items=[intelligence_from_domain(i) for i in items],
    )


@router.get("/feed", response_model=IntelligenceFeedResponse)
async def get_feed(
    asset: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    min_credibility: float | None = Query(default=None, ge=0, le=1),
    confirmed_only: bool = Query(default=False),
    cache: IntelligenceCache = Depends(get_intel_cache),
) -> IntelligenceFeedResponse:
    min_cred = Decimal(str(min_credibility)) if min_credibility is not None else None
    items = await cache.get_feed(
        asset=asset,
        limit=limit,
        min_credibility=min_cred,
        confirmed_only=confirmed_only,
    )
    return IntelligenceFeedResponse(
        generated_at=datetime.utcnow(),
        total=len(items),
        items=[intelligence_from_domain(i) for i in items],
    )


@router.get("/{item_id}/signals", response_model=IntelligenceSignalsResponse)
async def get_item_signals(
    item_id: UUID,
    catalog: SignalCatalog = Depends(get_signals),
    cache: IntelligenceCache = Depends(get_intel_cache),
) -> IntelligenceSignalsResponse:
    item = await cache.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intelligence item not found")
    signal_ids = await catalog.signals_for_intelligence(item_id)
    return IntelligenceSignalsResponse(
        intelligence_id=item_id,
        signal_ids=signal_ids,
    )


@router.get("/{item_id}", response_model=IntelligenceItemSchema)
async def get_item(
    item_id: UUID,
    cache: IntelligenceCache = Depends(get_intel_cache),
) -> IntelligenceItemSchema:
    item = await cache.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intelligence item not found")
    return intelligence_from_domain(item)
