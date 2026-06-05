"""Storage repository interfaces for signals-lab.

Defines abstract base classes for all data access layers.
Implementations live in timeseries.py (TimescaleDB) and relational.py (PostgreSQL).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..domain.enums import ObservationType, SignalStatus
from ..domain.evaluation import EvaluationMetrics, PaperPosition
from ..domain.features import FeatureBatch
from ..domain.market import AssetPair
from ..domain.signals import Signal


class TimeSeriesRepository(ABC):
    """Abstract interface for time-series observation storage.

    Implementations route data to the correct hypertable based on observation_type.
    """

    @abstractmethod
    async def store_observation(
        self, observation_type: ObservationType, data: Any
    ) -> bool:
        """Store a single observation in the appropriate hypertable."""
        ...

    @abstractmethod
    async def store_batch(
        self, observation_type: ObservationType, data_list: List[Any]
    ) -> int:
        """Store a batch of observations. Returns count of rows stored."""
        ...

    @abstractmethod
    async def query(
        self,
        observation_type: ObservationType,
        asset_pair: AssetPair,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> List[Any]:
        """Query observations in a time range for a given asset pair."""
        ...

    @abstractmethod
    async def get_latest(
        self, observation_type: ObservationType, asset_pair: AssetPair
    ) -> Optional[Any]:
        """Get the most recent observation for an asset pair."""
        ...

    @abstractmethod
    async def create_hypertable(
        self, table_name: str, time_column: str
    ) -> None:
        """Create a TimescaleDB hypertable if it doesn't exist."""
        ...


class SignalRepository(ABC):
    """Abstract interface for signal persistence."""

    @abstractmethod
    async def save(self, signal: Signal) -> UUID:
        """Persist a signal and return its ID."""
        ...

    @abstractmethod
    async def get(self, signal_id: UUID) -> Optional[Signal]:
        """Retrieve a signal by ID."""
        ...

    @abstractmethod
    async def list_active(
        self, asset_pair: Optional[AssetPair] = None, limit: int = 50
    ) -> List[Signal]:
        """List active signals, optionally filtered by asset pair."""
        ...

    @abstractmethod
    async def list_publishable(self, limit: int = 50) -> List[Signal]:
        """List signals eligible for publishing (high/extreme confidence)."""
        ...

    @abstractmethod
    async def update_status(
        self, signal_id: UUID, status: SignalStatus
    ) -> bool:
        """Update a signal's lifecycle status."""
        ...

    @abstractmethod
    async def get_history(
        self,
        asset_pair: Optional[AssetPair] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Signal]:
        """Query historical signals with optional filters."""
        ...


class EvaluationRepository(ABC):
    """Abstract interface for paper trading evaluation storage."""

    @abstractmethod
    async def save_position(self, position: PaperPosition) -> UUID:
        """Persist a paper position and return its ID."""
        ...

    @abstractmethod
    async def update_position(
        self, position_id: UUID, updates: Dict[str, Any]
    ) -> bool:
        """Update a paper position with new values."""
        ...

    @abstractmethod
    async def get_open_positions(self) -> List[PaperPosition]:
        """Get all currently open paper positions."""
        ...

    @abstractmethod
    async def get_closed_positions(
        self, start: datetime, end: datetime
    ) -> List[PaperPosition]:
        """Get positions closed within a time range."""
        ...

    @abstractmethod
    async def save_metrics(self, metrics: EvaluationMetrics) -> UUID:
        """Persist evaluation metrics and return ID."""
        ...

    @abstractmethod
    async def get_latest_metrics(self) -> Optional[EvaluationMetrics]:
        """Get the most recent evaluation metrics snapshot."""
        ...

    @abstractmethod
    async def get_metrics_history(
        self, start: datetime, end: datetime
    ) -> List[EvaluationMetrics]:
        """Get evaluation metrics history within a time range."""
        ...


class FeatureRepository(ABC):
    """Abstract interface for feature vector storage."""

    @abstractmethod
    async def store_vectors(self, batch: FeatureBatch) -> int:
        """Persist a batch of feature vectors. Returns count stored."""
        ...

    @abstractmethod
    async def query_vectors(
        self,
        asset_pair: AssetPair,
        feature_name: str,
        window: str,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> List[Any]:
        """Query feature vectors for a given feature/asset/window in a time range."""
        ...

    @abstractmethod
    async def get_latest_vectors(
        self,
        asset_pair: AssetPair,
        feature_names: List[str],
        window: str,
    ) -> Dict[str, Any]:
        """Get the most recent feature vectors for multiple features."""
        ...


class AssetRepository(ABC):
    """Abstract interface for asset pair management."""

    @abstractmethod
    async def save(self, asset_pair: AssetPair) -> bool:
        """Persist an asset pair."""
        ...

    @abstractmethod
    async def get(
        self, symbol: str, exchange: str
    ) -> Optional[AssetPair]:
        """Retrieve an asset pair by symbol and exchange."""
        ...

    @abstractmethod
    async def list_active(self) -> List[AssetPair]:
        """Get all active asset pairs."""
        ...

    @abstractmethod
    async def exists(self, symbol: str, exchange: str) -> bool:
        """Check if an asset pair exists."""
        ...