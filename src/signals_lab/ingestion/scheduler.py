"""Ingestion scheduler for orchestrating periodic data fetches."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from ..config import get_settings
from ..domain.enums import ObservationType
from ..storage.timeseries import TimescaleDBClient
from .base import BaseIngestor
from .market_ingestor import MarketIngestor
from .social_ingestor import SocialIngestor
from .onchain_ingestor import OnChainIngestor
from .event_ingestor import EventIngestor
from .intelligence_ingestor import IntelligenceIngestor

logger = structlog.get_logger(__name__)


class IngestionScheduler:
    """Orchestrates periodic data ingestion from all sources.

    Manages the lifecycle of ingestors, runs fetch cycles on configurable
    intervals, and persists observations to time-series storage.
    """

    def __init__(
        self,
        timeseries: TimescaleDBClient,
        ingestors: Optional[List[BaseIngestor]] = None,
    ) -> None:
        self._timeseries = timeseries
        self._ingestors = ingestors or []
        self._running = False
        self._tasks: List[asyncio.Task[Any]] = []
        self._logger = logger.bind(component="scheduler")

    @classmethod
    async def create(
        cls,
        timeseries: TimescaleDBClient,
    ) -> IngestionScheduler:
        """Create scheduler with all configured ingestors."""
        settings = get_settings()
        ingestors: List[BaseIngestor] = []

        if settings.ingestion.market.enabled:
            ingestors.append(MarketIngestor.from_settings())

        if settings.ingestion.social.enabled:
            ingestors.append(SocialIngestor.from_settings())

        if settings.ingestion.onchain.enabled:
            ingestors.append(OnChainIngestor.from_settings())

        if settings.ingestion.events.enabled:
            ingestors.append(EventIngestor.from_settings())

        if settings.ingestion.intelligence.enabled:
            ingestors.append(IntelligenceIngestor.from_settings())

        scheduler = cls(timeseries, ingestors)
        return scheduler

    async def start(self) -> None:
        """Start all ingestors and begin fetch cycles."""
        self._running = True
        self._logger.info("scheduler_starting", ingestor_count=len(self._ingestors))

        for ingestor in self._ingestors:
            await ingestor.start()

        # Launch fetch loops for each ingestor
        for ingestor in self._ingestors:
            task = asyncio.create_task(
                self._fetch_loop(ingestor),
                name=f"fetch_{ingestor.name}",
            )
            self._tasks.append(task)

        # Launch health check loop
        self._tasks.append(
            asyncio.create_task(self._health_check_loop(), name="health_check")
        )

        self._logger.info("scheduler_started")

    async def stop(self) -> None:
        """Gracefully stop all ingestors."""
        self._running = False
        self._logger.info("scheduler_stopping")

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)

        for ingestor in self._ingestors:
            await ingestor.stop()

        self._logger.info("scheduler_stopped")

    async def run_once(self) -> Dict[str, int]:
        """Run a single fetch cycle for all ingestors. Returns counts per ingestor."""
        results: Dict[str, int] = {}
        for ingestor in self._ingestors:
            count = await self._fetch_and_store(ingestor)
            results[ingestor.name] = count
        return results

    async def _fetch_loop(self, ingestor: BaseIngestor) -> None:
        """Periodic fetch loop for a single ingestor."""
        settings = get_settings()
        interval = getattr(
            getattr(settings.ingestion, ingestor.name.replace("_ingestor", ""), None),
            "interval_seconds",
            60,
        )

        self._logger.info(
            "fetch_loop_started",
            ingestor=ingestor.name,
            interval_seconds=interval,
        )

        while self._running:
            try:
                count = await self._fetch_and_store(ingestor)
                self._logger.info(
                    "fetch_cycle_complete",
                    ingestor=ingestor.name,
                    observations_fetched=count,
                )
            except asyncio.CancelledError:
                break
            except Exception:
                self._logger.error(
                    "fetch_cycle_failed",
                    ingestor=ingestor.name,
                    exc_info=True,
                )

            await asyncio.sleep(interval)

    async def _fetch_and_store(self, ingestor: BaseIngestor) -> int:
        """Fetch data from an ingestor and persist to time-series storage."""
        observations = await ingestor.fetch_all()
        if not observations:
            return 0

        count = await self._timeseries.store_batch(
            ingestor.observation_type, observations
        )
        return count

    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while self._running:
            try:
                for ingestor in self._ingestors:
                    statuses = await ingestor.health_check()
                    for name, status in statuses.items():
                        if status.value not in ("healthy",):
                            self._logger.warning(
                                "provider_unhealthy",
                                provider=name,
                                status=status.value,
                            )

                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception:
                self._logger.error("health_check_failed", exc_info=True)
                await asyncio.sleep(60)

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all ingestors and providers."""
        status: Dict[str, Any] = {
            "scheduler_running": self._running,
            "ingestors": {},
        }
        for ingestor in self._ingestors:
            provider_statuses = await ingestor.health_check()
            status["ingestors"][ingestor.name] = {
                "running": ingestor._running,
                "last_run": ingestor._last_run_at.isoformat() if ingestor._last_run_at else None,
                "providers": {k: v.value for k, v in provider_statuses.items()},
            }
        return status