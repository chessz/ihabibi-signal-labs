"""Social/sentiment data ingestion service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List
import random

import structlog

from ..config import ProviderConfig, get_settings
from ..domain.enums import ObservationType
from ..domain.market import AssetPair
from ..domain.social import SocialObservation
from .base import BaseIngestor, BaseProvider

logger = structlog.get_logger(__name__)


class MockSocialProvider(BaseProvider):
    """Mock social data provider for development and testing."""

    observation_type = ObservationType.SOCIAL

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._assets = config.assets or ["BTC", "ETH", "SOL"]

    async def fetch(self) -> List[SocialObservation]:
        """Generate mock social data."""
        observations: List[SocialObservation] = []
        for asset in self._assets:
            asset_pair = AssetPair(
                symbol=f"{asset}/USDT", base=asset, quote="USDT",
                exchange="mock", is_active=True,
            )
            observations.append(
                SocialObservation(
                    asset_pair=asset_pair,
                    timestamp=datetime.utcnow(),
                    mention_count=random.randint(100, 5000),
                    sentiment_score=Decimal(str(round(random.uniform(-0.5, 0.7), 2))),
                    sentiment_positive=random.randint(30, 2000),
                    sentiment_negative=random.randint(10, 1000),
                    sentiment_neutral=random.randint(50, 2000),
                    influencer_mentions=random.randint(0, 50),
                    social_dominance_pct=Decimal(str(round(random.uniform(1, 30), 2))),
                    topic_tags=random.sample(
                        ["bullish", "adoption", "defi", "nft", "layer2",
                         "regulation", "macro", "etf", "halving"],
                        k=random.randint(1, 4),
                    ),
                    source=self.name,
                )
            )
        return observations

    async def validate_response(self, response: Any) -> bool:
        return True


class SocialIngestor(BaseIngestor):
    """Social/sentiment data ingestion service."""

    observation_type = ObservationType.SOCIAL

    @classmethod
    def from_settings(cls) -> SocialIngestor:
        """Create ingestor from application settings."""
        settings = get_settings()
        svc = settings.ingestion.social

        providers: List[BaseProvider] = []
        for provider_config in svc.providers:
            providers.append(MockSocialProvider(provider_config))

        return cls(name="social_ingestor", providers=providers)