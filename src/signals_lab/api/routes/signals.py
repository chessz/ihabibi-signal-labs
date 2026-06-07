"""Signal publishing routes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from signals_lab.api.dependencies import get_signals
from signals_lab.api.schemas.signals import SignalListResponse, SignalSchema
from signals_lab.api.services.signal_catalog import SignalCatalog

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=SignalListResponse)
async def list_signals(
    publishable_only: bool = Query(default=False),
    catalog: SignalCatalog = Depends(get_signals),
) -> SignalListResponse:
    items = await catalog.list_signals(publishable_only=publishable_only)
    return SignalListResponse(
        generated_at=datetime.utcnow(),
        total=len(items),
        items=items,
    )


@router.get("/{signal_id}", response_model=SignalSchema)
async def get_signal(
    signal_id: UUID,
    catalog: SignalCatalog = Depends(get_signals),
) -> SignalSchema:
    signal = await catalog.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")
    return signal
