"""Base classes for data ingestion providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
import asyncio

import httpx
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..config import ProviderConfig
from ..domain.enums import ProviderStatus, ObservationType

logger = structlog.get_logger(__name__)


class BaseProvider(ABC):
    """Abstract base class for all data providers.

    Each provider subclass handles a specific external data source
    (exchange, social API, on-chain provider, news API).
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self._logger = logger.bind(provider=config.name, type=config.type)
        self._status: ProviderStatus = ProviderStatus.UNKNOWN
        self._last_success_at: Optional[datetime] = None
        self._last_error_at: Optional[datetime] = None
        self._consecutive_errors: int = 0
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def status(self) -> ProviderStatus:
        return self._status

    @property
    @abstractmethod
    def observation_type(self) -> ObservationType:
        """The type of observation this provider produces."""
        ...

    async def start(self) -> None:
        """Initialize HTTP client and validate connectivity."""
        api_key = self._get_api_key()
        headers: Dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._http_client = httpx.AsyncClient(
            base_url=self.config.base_url or "",
            headers=headers,
            timeout=self.config.timeout_seconds if hasattr(self.config, "timeout_seconds") else 30,
        )
        self._status = ProviderStatus.HEALTHY
        self._logger.info("provider_started")

    async def stop(self) -> None:
        """Gracefully shutdown the provider."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._logger.info("provider_stopped")

    @abstractmethod
    async def fetch(self) -> List[Any]:
        """Fetch data from the provider. Returns a list of observation objects."""
        ...

    @abstractmethod
    async def validate_response(self, response: Any) -> bool:
        """Validate the fetched data before processing."""
        ...

    async def health_check(self) -> ProviderStatus:
        """Perform a health check against the provider."""
        try:
            if self._consecutive_errors >= 3:
                self._status = ProviderStatus.DOWN
            elif self._consecutive_errors >= 1:
                self._status = ProviderStatus.DEGRADED
            else:
                self._status = ProviderStatus.HEALTHY
        except Exception:
            self._status = ProviderStatus.UNKNOWN
        return self._status

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variable."""
        if self.config.api_key_env:
            import os
            return os.environ.get(self.config.api_key_env)
        return None

    def _mark_success(self) -> None:
        """Update state after a successful fetch."""
        self._last_success_at = datetime.utcnow()
        self._consecutive_errors = 0

    def _mark_error(self, error: Exception) -> None:
        """Update state after a failed fetch."""
        self._last_error_at = datetime.utcnow()
        self._consecutive_errors += 1
        self._logger.error(
            "provider_fetch_error",
            error=str(error),
            consecutive_errors=self._consecutive_errors,
            exc_info=False,
        )


class BaseIngestor(ABC):
    """Abstract base class for ingestion services.

    Each ingestor manages multiple providers for a specific data domain
    (market, social, on-chain, events).
    """

    def __init__(self, name: str, providers: List[BaseProvider]) -> None:
        self.name = name
        self.providers = providers
        self._logger = logger.bind(ingestor=name)
        self._running = False
        self._last_run_at: Optional[datetime] = None

    @property
    @abstractmethod
    def observation_type(self) -> ObservationType:
        """The observation type produced by this ingestor."""
        ...

    async def start(self) -> None:
        """Start all providers."""
        self._running = True
        for provider in self.providers:
            try:
                await provider.start()
            except Exception:
                self._logger.error("provider_start_failed", provider=provider.name)

    async def stop(self) -> None:
        """Stop all providers."""
        self._running = False
        for provider in self.providers:
            try:
                await provider.stop()
            except Exception:
                self._logger.warning("provider_stop_failed", provider=provider.name)

    async def fetch_all(self) -> List[Any]:
        """Fetch data from all providers in parallel."""
        if not self._running:
            return []

        tasks = []
        for provider in self.providers:
            if provider.status in (ProviderStatus.HEALTHY, ProviderStatus.DEGRADED):
                tasks.append(self._fetch_from_provider(provider))

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_observations: List[Any] = []
        for result in results:
            if isinstance(result, Exception):
                self._logger.error("fetch_provider_failed", error=str(result))
            elif isinstance(result, list):
                all_observations.extend(result)

        self._last_run_at = datetime.utcnow()
        return all_observations

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPError, ConnectionError)),
    )
    async def _fetch_from_provider(self, provider: BaseProvider) -> List[Any]:
        """Fetch from a single provider with retry logic."""
        try:
            data = await provider.fetch()
            if await provider.validate_response(data):
                provider._mark_success()
                return data
            return []
        except Exception as e:
            provider._mark_error(e)
            raise

    async def health_check(self) -> Dict[str, ProviderStatus]:
        """Get health status of all providers."""
        statuses = {}
        for provider in self.providers:
            statuses[provider.name] = await provider.health_check()
        return statuses