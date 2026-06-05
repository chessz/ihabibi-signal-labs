"""TimescaleDB time-series storage implementation for signals-lab."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type
import json

import asyncpg
import structlog

from ..config import get_settings
from ..domain.enums import ObservationType
from ..domain.market import AssetPair, MarketObservation
from .repository import TimeSeriesRepository

logger = structlog.get_logger(__name__)

# Map observation types to hypertable names
OBSERVATION_TABLE_MAP: Dict[ObservationType, str] = {
    ObservationType.MARKET: "market_observations",
    ObservationType.SOCIAL: "social_observations",
    ObservationType.ONCHAIN: "onchain_observations",
    ObservationType.EVENTS: "event_observations",
    ObservationType.FEATURES: "feature_vectors",
}


class TimescaleDBClient(TimeSeriesRepository):
    """TimescaleDB client for high-volume time-series data.

    Uses asyncpg connection pool for async PostgreSQL operations.
    Hypertables are created automatically on initialization.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._logger = logger.bind(component="timeseries")

    @classmethod
    async def create(cls) -> TimescaleDBClient:
        """Factory method: create client from settings."""
        settings = get_settings()
        pool = await asyncpg.create_pool(
            settings.storage.timeseries.url,
            min_size=2,
            max_size=settings.storage.timeseries.pool_size,
            command_timeout=settings.storage.timeseries.pool_timeout,
        )
        client = cls(pool)
        await client._ensure_hypertables()
        return client

    async def _ensure_hypertables(self) -> None:
        """Create hypertables if they don't exist."""
        for obs_type, table_name in OBSERVATION_TABLE_MAP.items():
            await self._ensure_table_and_hypertable(obs_type, table_name)

    async def _ensure_table_and_hypertable(
        self, obs_type: ObservationType, table_name: str
    ) -> None:
        """Create table and hypertable for a given observation type."""
        async with self._pool.acquire() as conn:
            # Create table if not exists
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    time        TIMESTAMPTZ NOT NULL,
                    symbol      TEXT NOT NULL,
                    exchange    TEXT NOT NULL,
                    source      TEXT NOT NULL,
                    payload     JSONB NOT NULL,
                    UNIQUE (time, symbol, exchange, source)
                );
            """)

            # Convert to hypertable
            try:
                await conn.execute(f"""
                    SELECT create_hypertable('{table_name}', 'time', if_not_exists => TRUE);
                """)
            except Exception:
                # TimescaleDB extension may not be installed
                self._logger.warning(
                    "could_not_create_hypertable",
                    table=table_name,
                    exc_info=True,
                )

            # Create indexes
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol 
                ON {table_name} (symbol, time DESC);
            """)
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_time 
                ON {table_name} (time DESC);
            """)

    # ------------------------------------------------------------------
    # TimeSeriesRepository implementation
    # ------------------------------------------------------------------

    async def create_hypertable(self, table_name: str, time_column: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                SELECT create_hypertable('{table_name}', '{time_column}',
                                         if_not_exists => TRUE);
            """)

    async def store_observation(
        self, observation_type: ObservationType, data: Any
    ) -> bool:
        """Store a single observation."""
        table = OBSERVATION_TABLE_MAP[observation_type]
        symbol = self._extract_symbol(data)
        exchange = self._extract_exchange(data)
        source = getattr(data, "source", "unknown")
        timestamp = getattr(data, "timestamp", datetime.utcnow())

        payload = self._serialize(data)

        async with self._pool.acquire() as conn:
            try:
                await conn.execute(
                    f"""
                    INSERT INTO {table} (time, symbol, exchange, source, payload)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (time, symbol, exchange, source) DO NOTHING
                    """,
                    timestamp, symbol, exchange, source,
                    json.dumps(payload, default=str),
                )
                return True
            except Exception:
                self._logger.error(
                    "store_observation_failed",
                    table=table,
                    symbol=symbol,
                    exc_info=True,
                )
                return False

    async def store_batch(
        self, observation_type: ObservationType, data_list: List[Any]
    ) -> int:
        """Store a batch of observations using COPY protocol."""
        if not data_list:
            return 0

        table = OBSERVATION_TABLE_MAP[observation_type]
        count = 0

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for data in data_list:
                    symbol = self._extract_symbol(data)
                    exchange = self._extract_exchange(data)
                    source = getattr(data, "source", "unknown")
                    timestamp = getattr(data, "timestamp", datetime.utcnow())
                    payload = self._serialize(data)

                    try:
                        await conn.execute(
                            f"""
                            INSERT INTO {table} (time, symbol, exchange, source, payload)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (time, symbol, exchange, source) DO NOTHING
                            """,
                            timestamp, symbol, exchange, source,
                            json.dumps(payload, default=str),
                        )
                        count += 1
                    except Exception:
                        self._logger.error(
                            "store_batch_item_failed",
                            table=table,
                            symbol=symbol,
                            exc_info=True,
                        )

        return count

    async def query(
        self,
        observation_type: ObservationType,
        asset_pair: AssetPair,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Query observations in a time range."""
        table = OBSERVATION_TABLE_MAP[observation_type]
        symbol = asset_pair.normalized_symbol

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT time, symbol, exchange, source, payload
                FROM {table}
                WHERE symbol = $1
                  AND time >= $2
                  AND time <= $3
                ORDER BY time DESC
                LIMIT $4
                """,
                symbol, start_time, end_time, limit,
            )
            return [dict(row) for row in rows]

    async def get_latest(
        self, observation_type: ObservationType, asset_pair: AssetPair
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent observation."""
        table = OBSERVATION_TABLE_MAP[observation_type]
        symbol = asset_pair.normalized_symbol

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT time, symbol, exchange, source, payload
                FROM {table}
                WHERE symbol = $1
                ORDER BY time DESC
                LIMIT 1
                """,
                symbol,
            )
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_symbol(data: Any) -> str:
        """Extract normalized symbol from observation data."""
        if hasattr(data, "asset_pair"):
            return data.asset_pair.normalized_symbol
        if hasattr(data, "symbol"):
            return data.symbol
        return "unknown"

    @staticmethod
    def _extract_exchange(data: Any) -> str:
        """Extract exchange from observation data."""
        if hasattr(data, "asset_pair"):
            return data.asset_pair.exchange
        return "unknown"

    @staticmethod
    def _serialize(data: Any) -> Dict[str, Any]:
        """Serialize a domain object to a JSON-compatible dict."""
        if hasattr(data, "model_dump"):
            return data.model_dump(mode="json")
        if hasattr(data, "dict"):
            return data.dict()
        return dict(data) if hasattr(data, "__dict__") else {"value": str(data)}

    async def close(self) -> None:
        """Close the connection pool."""
        await self._pool.close()