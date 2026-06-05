"""Event/geopolitical data ingestion service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List
import random
import uuid

import structlog

from ..config import ProviderConfig, get_settings
from ..domain.enums import ObservationType
from ..domain.events import EventObservation
from .base import BaseIngestor, BaseProvider

logger = structlog.get_logger(__name__)

_MOCK_EVENTS = [
    ("SEC approves spot Ethereum ETF", "etf", 4, ["ETH", "BTC"]),
    ("Fed signals rate cut in September", "macro", 3, ["BTC", "ETH"]),
    ("Binance security incident reported", "exchange_incident", 5, ["BTC", "BNB"]),
    ("New crypto regulation proposed in EU", "regulatory", 3, ["BTC", "ETH"]),
    ("Tech stocks rally boosts crypto sentiment", "macro", 2, ["BTC", "ETH", "SOL"]),
    ("Whale moves $500M in BTC off exchange", "technical", 2, ["BTC"]),
    ("DeFi protocol suffers $50M exploit", "technical", 4, ["ETH"]),
    ("Bitcoin ETF sees record inflows", "etf", 3, ["BTC"]),
    ("Geopolitical tensions rise in Middle East", "geopolitical", 5, ["BTC", "ETH"]),
    ("Bank of Japan raises interest rates", "macro", 3, ["BTC", "ETH"]),
]

_REGIONS = ["NA", "EU", "ASIA", "ME", "GLOBAL"]


class MockEventProvider(BaseProvider):
    """Mock events/news provider for development and testing."""

    observation_type = ObservationType.EVENTS

    async def fetch(self) -> List[EventObservation]:
        """Generate mock event data."""
        observations: List[EventObservation] = []
        num_events = random.randint(1, 4)
        selected = random.sample(_MOCK_EVENTS, min(num_events, len(_MOCK_EVENTS)))

        for title, event_type, severity, affected in selected:
            observations.append(
                EventObservation(
                    timestamp=datetime.utcnow(),
                    event_type=event_type,
                    title=title,
                    description=f"Mock event: {title}",
                    severity=severity,
                    affected_assets=affected,
                    region=random.choice(_REGIONS),
                    market_impact_estimate=Decimal(str(round(random.uniform(0, 1), 2))),
                    tags=[event_type],
                    source=self.name,
                    is_breaking=random.random() < 0.2,
                )
            )
        return observations

    async def validate_response(self, response: Any) -> bool:
        return True


class EventIngestor(BaseIngestor):
    """Events/geopolitical data ingestion service."""

    observation_type = ObservationType.EVENTS

    @classmethod
    def from_settings(cls) -> EventIngestor:
        """Create ingestor from application settings."""
        settings = get_settings()
        svc = settings.ingestion.events

        providers: List[BaseProvider] = []
        for provider_config in svc.providers:
            providers.append(MockEventProvider(provider_config))

        return cls(name="event_ingestor", providers=providers)