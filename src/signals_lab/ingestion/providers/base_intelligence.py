"""Base class for Tier A/B intelligence providers."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from signals_lab.domain.enums import ObservationType
from signals_lab.domain.intelligence import RawIntelligenceRecord
from signals_lab.ingestion.base import BaseProvider


class BaseIntelligenceProvider(BaseProvider):
    """Fetches raw intelligence records from external sources."""

    observation_type = ObservationType.INTELLIGENCE

    @abstractmethod
    async def fetch(self) -> list[RawIntelligenceRecord]:
        """Fetch raw records from provider."""

    async def validate_response(self, response: Any) -> bool:
        return isinstance(response, list)
