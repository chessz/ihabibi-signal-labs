"""On-chain data ingestion service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List
import random

import structlog

from ..config import ProviderConfig, get_settings
from ..domain.enums import ObservationType
from ..domain.market import AssetPair
from ..domain.onchain import OnChainObservation
from .base import BaseIngestor, BaseProvider

logger = structlog.get_logger(__name__)


class MockOnChainProvider(BaseProvider):
    """Mock on-chain data provider for development and testing."""

    observation_type = ObservationType.ONCHAIN

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._assets = config.assets or ["BTC", "ETH", "SOL"]

    async def fetch(self) -> List[OnChainObservation]:
        """Generate mock on-chain data."""
        observations: List[OnChainObservation] = []
        for asset in self._assets:
            asset_pair = AssetPair(
                symbol=f"{asset}/USDT", base=asset, quote="USDT",
                exchange="onchain", is_active=True,
            )
            observations.append(
                OnChainObservation(
                    asset_pair=asset_pair,
                    timestamp=datetime.utcnow(),
                    exchange_inflow_usd=Decimal(str(random.randint(100000, 50000000))),
                    exchange_outflow_usd=Decimal(str(random.randint(100000, 50000000))),
                    whale_transaction_count=random.randint(0, 20),
                    whale_transaction_volume_usd=Decimal(str(random.randint(1000000, 100000000))),
                    stablecoin_minted_usd=Decimal(str(random.randint(0, 5000000))),
                    stablecoin_redeemed_usd=Decimal(str(random.randint(0, 3000000))),
                    supply_on_exchanges_pct=Decimal(str(round(random.uniform(5, 20), 2))),
                    large_holder_net_flow_usd=Decimal(str(random.randint(-5000000, 5000000))),
                    active_addresses=random.randint(500000, 2000000),
                    transaction_count=random.randint(100000, 500000),
                    source=self.name,
                )
            )
        return observations

    async def validate_response(self, response: Any) -> bool:
        return True


class OnChainIngestor(BaseIngestor):
    """On-chain data ingestion service."""

    observation_type = ObservationType.ONCHAIN

    @classmethod
    def from_settings(cls) -> OnChainIngestor:
        """Create ingestor from application settings."""
        settings = get_settings()
        svc = settings.ingestion.onchain

        providers: List[BaseProvider] = []
        for provider_config in svc.providers:
            providers.append(MockOnChainProvider(provider_config))

        return cls(name="onchain_ingestor", providers=providers)