"""Multi-source intelligence ingestion service."""

from __future__ import annotations

import asyncio
from datetime import datetime

import structlog

from signals_lab.config import ProviderConfig, get_settings
from signals_lab.domain.enums import ObservationType, ProviderStatus
from signals_lab.domain.intelligence import IntelligenceItem, RawIntelligenceRecord
from signals_lab.ingestion.base import BaseIngestor
from signals_lab.ingestion.providers.base_intelligence import BaseIntelligenceProvider
from signals_lab.ingestion.providers.news.cryptocurrency_cv import CryptocurrencyCvProvider
from signals_lab.ingestion.providers.news.rss_feed import RssFanInProvider
from signals_lab.intelligence.engine import IntelligencePipeline

logger = structlog.get_logger(__name__)

_PROVIDER_REGISTRY: dict[str, type[BaseIntelligenceProvider]] = {
    "cryptocurrency_cv": CryptocurrencyCvProvider,
    "rss_fan_in": RssFanInProvider,
}


def _provider_enabled(config: ProviderConfig) -> bool:
    enabled = getattr(config, "enabled", True)
    if isinstance(enabled, str):
        return enabled.lower() in ("true", "1", "yes")
    return bool(enabled)


def build_intelligence_providers(configs: list[ProviderConfig]) -> list[BaseIntelligenceProvider]:
    providers: list[BaseIntelligenceProvider] = []
    for cfg in configs:
        if not _provider_enabled(cfg):
            continue
        cls = _PROVIDER_REGISTRY.get(cfg.name)
        if cls is None:
            logger.warning("unknown_intelligence_provider", name=cfg.name)
            continue
        providers.append(cls(cfg))
    return providers


class IntelligenceIngestor(BaseIngestor):
    """Fetch Tier A intelligence, normalize, dedup, and score."""

    observation_type = ObservationType.INTELLIGENCE

    def __init__(
        self,
        name: str,
        providers: list[BaseIntelligenceProvider],
        pipeline: IntelligencePipeline | None = None,
    ) -> None:
        super().__init__(name, providers)  # type: ignore[arg-type]
        self._pipeline = pipeline or IntelligencePipeline()
        self._last_items: list[IntelligenceItem] = []
        self._logger = logger.bind(ingestor=name)

    @classmethod
    def from_settings(cls) -> IntelligenceIngestor:
        settings = get_settings()
        svc = settings.ingestion.intelligence
        providers = build_intelligence_providers(list(svc.providers))
        return cls(name="intelligence_ingestor", providers=providers)

    async def fetch_all(self) -> list[IntelligenceItem]:
        """Fetch from all Tier A providers and run intelligence pipeline."""
        if not self._running and self.providers:
            # Allow one-shot fetch without scheduler start()
            pass

        raw_records: list[RawIntelligenceRecord] = []
        tasks = [self._fetch_raw(provider) for provider in self.providers]
        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                self._logger.error("intelligence_provider_failed", error=str(result))
            elif isinstance(result, list):
                raw_records.extend(result)

        items = self._pipeline.process(raw_records)
        self._last_items = items
        self._last_run_at = datetime.utcnow()
        return items

    async def _fetch_raw(self, provider: BaseIntelligenceProvider) -> list[RawIntelligenceRecord]:
        try:
            if provider._http_client is None:
                await provider.start()
            data = await provider.fetch()
            if await provider.validate_response(data):
                provider._mark_success()
                return data
            return []
        except Exception as exc:
            provider._mark_error(exc)
            self._logger.warning(
                "intelligence_fetch_error",
                provider=provider.name,
                error=str(exc),
            )
            return []

    @property
    def last_items(self) -> list[IntelligenceItem]:
        return list(self._last_items)

    async def health_check(self) -> dict[str, ProviderStatus]:
        statuses: dict[str, ProviderStatus] = {}
        for provider in self.providers:
            statuses[provider.name] = await provider.health_check()
        return statuses

    async def fetch_raw_only(self) -> list[RawIntelligenceRecord]:
        """Fetch without pipeline — for debugging."""
        items: list[RawIntelligenceRecord] = []
        for provider in self.providers:
            items.extend(await self._fetch_raw(provider))
        return items
