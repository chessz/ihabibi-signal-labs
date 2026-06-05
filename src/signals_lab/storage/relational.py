"""PostgreSQL relational storage implementation for signals-lab."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
import json

import asyncpg
import structlog

from ..config import get_settings
from ..domain.enums import ConfidenceBand, MarketRegime, SignalClass, SignalStatus, PositionStatus
from ..domain.evaluation import EvaluationMetrics, PaperPosition
from ..domain.market import AssetPair
from ..domain.signals import Signal

logger = structlog.get_logger(__name__)


class PostgreSQLClient:
    """PostgreSQL client for relational metadata, signals, and evaluation.

    Uses asyncpg for async database operations.
    Manages schema creation on first connection.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._logger = logger.bind(component="relational")

    @classmethod
    async def create(cls) -> PostgreSQLClient:
        """Factory method: create client from settings."""
        settings = get_settings()
        pool = await asyncpg.create_pool(
            settings.storage.relational.url,
            min_size=2,
            max_size=settings.storage.relational.pool_size,
            command_timeout=settings.storage.relational.pool_timeout,
        )
        client = cls(pool)
        await client._ensure_schema()
        return client

    async def _ensure_schema(self) -> None:
        """Create relational tables if they don't exist."""
        async with self._pool.acquire() as conn:
            # Asset pairs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS asset_pairs (
                    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    symbol      TEXT NOT NULL,
                    base        TEXT NOT NULL,
                    quote       TEXT NOT NULL,
                    exchange    TEXT NOT NULL,
                    is_active   BOOLEAN DEFAULT TRUE,
                    metadata    JSONB DEFAULT '{}',
                    created_at  TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE (symbol, exchange)
                );
            """)

            # Signals
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id           UUID PRIMARY KEY,
                    asset_pair_id       UUID REFERENCES asset_pairs(id),
                    symbol              TEXT NOT NULL,
                    exchange            TEXT NOT NULL,
                    signal_class        TEXT NOT NULL,
                    side                TEXT NOT NULL,
                    confidence_score    NUMERIC(5,2) NOT NULL,
                    confidence_band     TEXT NOT NULL,
                    generated_at        TIMESTAMPTZ NOT NULL,
                    expiry_at           TIMESTAMPTZ,
                    regime              TEXT DEFAULT 'unknown',
                    thesis              TEXT NOT NULL,
                    contributing_factors JSONB DEFAULT '[]',
                    invalidation_condition TEXT NOT NULL,
                    suggested_stop      JSONB,
                    suggested_sell      JSONB,
                    expected_holding_horizon TEXT DEFAULT '4h',
                    provenance          JSONB DEFAULT '{}',
                    status              TEXT DEFAULT 'active',
                    entry_price         NUMERIC,
                    target_price        NUMERIC,
                    metadata            JSONB DEFAULT '{}',
                    created_at          TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_symbol 
                ON signals (symbol, generated_at DESC);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_status 
                ON signals (status, generated_at DESC);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_confidence 
                ON signals (confidence_band, generated_at DESC);
            """)

            # Paper positions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS paper_positions (
                    position_id                 UUID PRIMARY KEY,
                    signal_id                   UUID REFERENCES signals(signal_id),
                    asset_pair_id               UUID REFERENCES asset_pairs(id),
                    symbol                      TEXT NOT NULL,
                    exchange                    TEXT NOT NULL,
                    side                        TEXT NOT NULL,
                    entry_price                 NUMERIC NOT NULL,
                    entry_time                  TIMESTAMPTZ NOT NULL,
                    quantity                    NUMERIC NOT NULL,
                    notional_usd                NUMERIC NOT NULL,
                    stop_price                  NUMERIC,
                    target_price                NUMERIC,
                    status                      TEXT DEFAULT 'open',
                    exit_price                  NUMERIC,
                    exit_time                   TIMESTAMPTZ,
                    exit_reason                 TEXT,
                    pnl_usd                     NUMERIC,
                    pnl_pct                     NUMERIC,
                    fees_usd                    NUMERIC DEFAULT 0,
                    slippage_usd                NUMERIC DEFAULT 0,
                    max_favorable_excursion_pct NUMERIC,
                    max_adverse_excursion_pct   NUMERIC,
                    holding_period_hours        NUMERIC,
                    is_win                      BOOLEAN,
                    signal_confidence_band      TEXT,
                    signal_regime               TEXT,
                    signal_class                TEXT,
                    tags                        JSONB DEFAULT '{}',
                    created_at                  TIMESTAMPTZ DEFAULT NOW(),
                    updated_at                  TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # Evaluation metrics
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_metrics (
                    metrics_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    period_start            TIMESTAMPTZ NOT NULL,
                    period_end              TIMESTAMPTZ NOT NULL,
                    metrics_payload         JSONB NOT NULL,
                    generated_at            TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # Worker runs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS worker_runs (
                    run_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    worker_name     TEXT NOT NULL,
                    started_at      TIMESTAMPTZ DEFAULT NOW(),
                    completed_at    TIMESTAMPTZ,
                    status          TEXT DEFAULT 'running',
                    result_payload   JSONB DEFAULT '{}',
                    error_message   TEXT
                );
            """)

            # API keys
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name            TEXT NOT NULL UNIQUE,
                    key_hash        TEXT NOT NULL,
                    permissions     TEXT[] NOT NULL DEFAULT '{}',
                    is_active       BOOLEAN DEFAULT TRUE,
                    created_at      TIMESTAMPTZ DEFAULT NOW(),
                    last_used_at    TIMESTAMPTZ
                );
            """)

    # ------------------------------------------------------------------
    # Asset pairs
    # ------------------------------------------------------------------

    async def save_asset(self, asset_pair: AssetPair) -> bool:
        """Persist an asset pair."""
        async with self._pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO asset_pairs (symbol, base, quote, exchange, is_active, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (symbol, exchange) DO UPDATE SET
                        is_active = EXCLUDED.is_active,
                        metadata = EXCLUDED.metadata
                    """,
                    asset_pair.symbol,
                    asset_pair.base,
                    asset_pair.quote,
                    asset_pair.exchange,
                    asset_pair.is_active,
                    json.dumps(asset_pair.metadata),
                )
                return True
            except Exception:
                self._logger.error("save_asset_failed", symbol=asset_pair.symbol, exc_info=True)
                return False

    async def get_asset(self, symbol: str, exchange: str) -> Optional[AssetPair]:
        """Retrieve an asset pair."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM asset_pairs WHERE symbol = $1 AND exchange = $2",
                symbol, exchange,
            )
            if row:
                return AssetPair(
                    symbol=row["symbol"],
                    base=row["base"],
                    quote=row["quote"],
                    exchange=row["exchange"],
                    is_active=row["is_active"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
            return None

    async def list_active_assets(self) -> List[AssetPair]:
        """Get all active asset pairs."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM asset_pairs WHERE is_active = TRUE ORDER BY symbol"
            )
            return [
                AssetPair(
                    symbol=r["symbol"],
                    base=r["base"],
                    quote=r["quote"],
                    exchange=r["exchange"],
                    is_active=r["is_active"],
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                )
                for r in rows
            ]

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    async def save_signal(self, signal: Signal) -> UUID:
        """Persist a signal."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO signals (
                    signal_id, symbol, exchange, signal_class, side,
                    confidence_score, confidence_band, generated_at, expiry_at,
                    regime, thesis, contributing_factors, invalidation_condition,
                    suggested_stop, suggested_sell, expected_holding_horizon,
                    provenance, status, entry_price, target_price, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9,
                    $10, $11, $12, $13, $14, $15, $16,
                    $17, $18, $19, $20, $21
                )
                """,
                signal.signal_id,
                signal.asset_pair.symbol,
                signal.asset_pair.exchange,
                signal.signal_class.value,
                signal.side.value,
                signal.confidence_score,
                signal.confidence_band.value,
                signal.generated_at,
                signal.expiry_at,
                signal.regime.value,
                signal.thesis,
                json.dumps([f.model_dump(mode="json") for f in signal.contributing_factors]),
                signal.invalidation_condition,
                json.dumps(signal.suggested_stop.model_dump(mode="json")) if signal.suggested_stop else None,
                json.dumps(signal.suggested_sell.model_dump(mode="json")) if signal.suggested_sell else None,
                signal.expected_holding_horizon,
                json.dumps(signal.provenance.model_dump(mode="json")),
                signal.status.value,
                str(signal.entry_price) if signal.entry_price else None,
                str(signal.target_price) if signal.target_price else None,
                json.dumps(signal.metadata),
            )
            return signal.signal_id

    async def get_signal(self, signal_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve a signal by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM signals WHERE signal_id = $1", signal_id
            )
            return dict(row) if row else None

    async def list_active_signals(
        self, symbol: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List active signals."""
        async with self._pool.acquire() as conn:
            if symbol:
                rows = await conn.fetch(
                    """SELECT * FROM signals 
                       WHERE status = 'active' AND symbol = $1 
                       ORDER BY generated_at DESC LIMIT $2""",
                    symbol, limit,
                )
            else:
                rows = await conn.fetch(
                    """SELECT * FROM signals 
                       WHERE status = 'active' 
                       ORDER BY generated_at DESC LIMIT $1""",
                    limit,
                )
            return [dict(r) for r in rows]

    async def list_publishable_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List high/extreme confidence active signals."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM signals 
                   WHERE status = 'active' 
                     AND confidence_band IN ('high', 'extreme')
                   ORDER BY confidence_score DESC, generated_at DESC 
                   LIMIT $1""",
                limit,
            )
            return [dict(r) for r in rows]

    async def update_signal_status(
        self, signal_id: UUID, status: SignalStatus
    ) -> bool:
        """Update signal status."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE signals SET status = $1 WHERE signal_id = $2",
                status.value, signal_id,
            )
            return True

    # ------------------------------------------------------------------
    # Paper positions
    # ------------------------------------------------------------------

    async def save_position(self, position: PaperPosition) -> UUID:
        """Persist a paper position."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO paper_positions (
                    position_id, signal_id, symbol, exchange, side,
                    entry_price, entry_time, quantity, notional_usd,
                    stop_price, target_price, status, fees_usd, slippage_usd,
                    signal_confidence_band, signal_regime, signal_class, tags
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9,
                    $10, $11, $12, $13, $14,
                    $15, $16, $17, $18
                )
                """,
                position.position_id,
                position.signal_id,
                position.asset_pair.symbol,
                position.asset_pair.exchange,
                position.side.value,
                position.entry_price,
                position.entry_time,
                position.quantity,
                position.notional_usd,
                str(position.stop_price) if position.stop_price else None,
                str(position.target_price) if position.target_price else None,
                position.status.value,
                position.fees_usd,
                position.slippage_usd,
                position.signal_confidence_band.value if position.signal_confidence_band else None,
                position.signal_regime.value if position.signal_regime else None,
                position.signal_class.value if position.signal_class else None,
                json.dumps(position.tags),
            )
            return position.position_id

    async def update_position(
        self, position_id: UUID, updates: Dict[str, Any]
    ) -> bool:
        """Update a paper position."""
        set_clauses = []
        values: List[Any] = []
        idx = 1

        for key, value in updates.items():
            set_clauses.append(f"{key} = ${idx}")
            values.append(value)
            idx += 1

        if not set_clauses:
            return False

        set_clauses.append(f"updated_at = NOW()")
        values.append(position_id)

        async with self._pool.acquire() as conn:
            await conn.execute(
                f"UPDATE paper_positions SET {', '.join(set_clauses)} WHERE position_id = ${idx}",
                *values,
            )
            return True

    async def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open paper positions."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM paper_positions WHERE status = 'open' ORDER BY entry_time"
            )
            return [dict(r) for r in rows]

    async def get_closed_positions(
        self, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        """Get positions closed within a time range."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM paper_positions 
                   WHERE status IN ('closed', 'stopped', 'expired')
                     AND exit_time >= $1 AND exit_time <= $2
                   ORDER BY exit_time DESC""",
                start, end,
            )
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Evaluation metrics
    # ------------------------------------------------------------------

    async def save_metrics(self, metrics: EvaluationMetrics) -> UUID:
        """Persist evaluation metrics."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO evaluation_metrics (period_start, period_end, metrics_payload)
                VALUES ($1, $2, $3)
                RETURNING metrics_id
                """,
                metrics.period_start,
                metrics.period_end,
                json.dumps(metrics.model_dump(mode="json"), default=str),
            )
            return row["metrics_id"] if row else UUID(int=0)

    async def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """Get the most recent evaluation metrics."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM evaluation_metrics ORDER BY generated_at DESC LIMIT 1"
            )
            return dict(row) if row else None

    async def close(self) -> None:
        """Close the connection pool."""
        await self._pool.close()