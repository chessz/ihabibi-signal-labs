"""Market data ingestion service (exchanges, OHLCV, order books)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

import httpx
import structlog

from ..config import ProviderConfig, IngestionServiceSettings, get_settings
from ..domain.enums import ObservationType
from ..domain.market import AssetPair, Candle, MarketObservation, MarketDataBatch
from .base import BaseIngestor, BaseProvider

logger = structlog.get_logger(__name__)


class BinanceMarketProvider(BaseProvider):
    """Binance REST API market data provider."""

    observation_type = ObservationType.MARKET

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._symbols = config.symbols or ["BTC/USDT"]

    async def fetch(self) -> List[MarketObservation]:
        """Fetch current market data for all configured symbols."""
        if not self._http_client:
            return []

        observations: List[MarketObservation] = []
        for symbol in self._symbols:
            try:
                obs = await self._fetch_symbol(symbol)
                if obs:
                    observations.append(obs)
            except Exception:
                self._logger.error("fetch_symbol_failed", symbol=symbol, exc_info=True)

        return observations

    async def _fetch_symbol(self, symbol: str) -> Optional[MarketObservation]:
        """Fetch market data for a single symbol."""
        if not self._http_client:
            return None

        binance_symbol = symbol.replace("/", "")
        try:
            # 24hr ticker
            resp = await self._http_client.get(
                "/api/v3/ticker/24hr",
                params={"symbol": binance_symbol},
            )
            resp.raise_for_status()
            ticker = resp.json()

            # Recent trades for spread estimate
            trades_resp = await self._http_client.get(
                "/api/v3/trades",
                params={"symbol": binance_symbol, "limit": 10},
            )
            trades_resp.raise_for_status()
            trades = trades_resp.json()

            base, quote = symbol.split("/")
            asset_pair = AssetPair(
                symbol=symbol,
                base=base,
                quote=quote,
                exchange="binance",
                is_active=True,
            )

            # Estimate spread from last trade prices
            if trades:
                prices = [Decimal(str(t["price"])) for t in trades]
                max_price = max(prices)
                min_price = min(prices)
                if min_price > 0:
                    spread_bps = int(((max_price - min_price) / min_price) * 10000)
                else:
                    spread_bps = None
            else:
                spread_bps = None

            return MarketObservation(
                asset_pair=asset_pair,
                timestamp=datetime.utcnow(),
                open=Decimal(str(ticker["openPrice"])),
                high=Decimal(str(ticker["highPrice"])),
                low=Decimal(str(ticker["lowPrice"])),
                close=Decimal(str(ticker["lastPrice"])),
                volume=Decimal(str(ticker["volume"])),
                spread_bps=spread_bps,
                source=self.name,
            )
        except Exception:
            raise

    async def validate_response(self, response: Any) -> bool:
        """Validate Binance API response."""
        if isinstance(response, list):
            return len(response) > 0
        return True


class MockMarketProvider(BaseProvider):
    """Mock market provider for development and testing."""

    observation_type = ObservationType.MARKET

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._symbols = config.symbols or ["BTC/USDT", "ETH/USDT"]

    async def fetch(self) -> List[MarketObservation]:
        """Generate mock market data."""
        import random

        observations: List[MarketObservation] = []
        for symbol in self._symbols:
            base, quote = symbol.split("/")
            asset_pair = AssetPair(
                symbol=symbol, base=base, quote=quote,
                exchange="mock", is_active=True,
            )
            base_price = 50000 if base == "BTC" else 3000 if base == "ETH" else 100
            price = Decimal(str(base_price * (1 + random.uniform(-0.02, 0.02))))
            observations.append(
                MarketObservation(
                    asset_pair=asset_pair,
                    timestamp=datetime.utcnow(),
                    open=price,
                    high=price * Decimal("1.01"),
                    low=price * Decimal("0.99"),
                    close=price,
                    volume=Decimal(str(random.randint(1000, 100000))),
                    spread_bps=random.randint(1, 10),
                    source=self.name,
                )
            )
        return observations

    async def validate_response(self, response: Any) -> bool:
        return True


class MarketIngestor(BaseIngestor):
    """Market data ingestion service."""

    observation_type = ObservationType.MARKET

    @classmethod
    def from_settings(cls) -> MarketIngestor:
        """Create ingestor from application settings."""
        settings = get_settings()
        svc = settings.ingestion.market

        providers: List[BaseProvider] = []
        for provider_config in svc.providers:
            if not provider_config.api_key_env or provider_config.type == "mock":
                providers.append(MockMarketProvider(provider_config))
            elif provider_config.name == "binance":
                providers.append(BinanceMarketProvider(provider_config))
            else:
                providers.append(MockMarketProvider(provider_config))

        return cls(name="market_ingestor", providers=providers)