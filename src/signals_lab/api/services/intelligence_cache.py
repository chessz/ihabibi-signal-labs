"""In-memory intelligence cache with live ingest refresh."""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
from uuid import UUID

import structlog

from signals_lab.api.services.seed_intelligence import SEED_INTELLIGENCE_ITEMS
from signals_lab.domain.intelligence import IntelligenceItem
from signals_lab.ingestion.intelligence_ingestor import IntelligenceIngestor

logger = structlog.get_logger(__name__)

_CACHE_TTL_SECONDS = 60
_MIN_CONFIRMATION = 2


def _sort_ticker_key(item: IntelligenceItem) -> tuple[int, float, float]:
    confirmed = 1 if item.cross_source_confirmation_count >= _MIN_CONFIRMATION else 0
    return (
        confirmed,
        float(item.novelty_score),
        item.observed_at.timestamp(),
    )


class IntelligenceCache:
    """Thread-safe async cache backed by IntelligenceIngestor."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._items: dict[UUID, IntelligenceItem] = {}
        self._last_refresh: datetime | None = None
        self._ingestor: IntelligenceIngestor | None = None
        self._seeded = False

    def _ensure_seed(self) -> None:
        if self._seeded:
            return
        for item in SEED_INTELLIGENCE_ITEMS:
            self._items[item.id] = item
        self._seeded = True

    async def refresh(self, force: bool = False) -> None:
        async with self._lock:
            self._ensure_seed()
            now = datetime.utcnow()
            if (
                not force
                and self._last_refresh
                and (now - self._last_refresh).total_seconds() < _CACHE_TTL_SECONDS
            ):
                return

            try:
                if self._ingestor is None:
                    self._ingestor = IntelligenceIngestor.from_settings()
                live_items = await self._ingestor.fetch_all()
                for item in live_items:
                    self._items[item.id] = item
                logger.info("intelligence_cache_refreshed", live_count=len(live_items))
            except Exception:
                logger.warning("intelligence_cache_refresh_failed", exc_info=True)

            self._last_refresh = now

    async def list_items(self) -> list[IntelligenceItem]:
        await self.refresh()
        return list(self._items.values())

    async def get_item(self, item_id: UUID) -> IntelligenceItem | None:
        await self.refresh()
        return self._items.get(item_id)

    async def get_ticker(self, limit: int = 12) -> list[IntelligenceItem]:
        items = await self.list_items()
        ranked = sorted(items, key=_sort_ticker_key, reverse=True)
        return ranked[:limit]

    async def get_feed(
        self,
        *,
        asset: str | None = None,
        limit: int = 50,
        since: datetime | None = None,
        min_credibility: Decimal | None = None,
        confirmed_only: bool = False,
    ) -> list[IntelligenceItem]:
        items = await self.list_items()
        filtered: list[IntelligenceItem] = []
        for item in items:
            if since and item.observed_at < since:
                continue
            if asset and asset.upper() not in [t.upper() for t in item.asset_tags]:
                continue
            if min_credibility is not None and item.credibility_score < min_credibility:
                continue
            if confirmed_only and item.cross_source_confirmation_count < _MIN_CONFIRMATION:
                continue
            filtered.append(item)

        filtered.sort(key=lambda i: i.observed_at, reverse=True)
        return filtered[:limit]

    async def last_refresh_at(self) -> datetime | None:
        return self._last_refresh



class _CacheHolder:
    instance: IntelligenceCache | None = None


def get_intelligence_cache() -> IntelligenceCache:
    if _CacheHolder.instance is None:
        _CacheHolder.instance = IntelligenceCache()
    return _CacheHolder.instance
