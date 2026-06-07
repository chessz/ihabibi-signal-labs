"""In-memory signal catalog with intelligence attribution links."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from signals_lab.api.schemas.intelligence import intelligence_from_domain
from signals_lab.api.schemas.signals import SignalSchema, signal_to_schema
from signals_lab.api.services.intelligence_cache import IntelligenceCache, get_intelligence_cache
from signals_lab.api.services.seed_intelligence import (
    ID_BTC_STRATEGY,
    ID_BTC_YIELD,
    ID_ETH_DERIVATIVES,
    SEED_INTELLIGENCE_BY_ID,
)

SIGNAL_BTC = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
SIGNAL_ETH = UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")

SIGNAL_INTELLIGENCE_LINKS: dict[UUID, list[tuple[UUID, Decimal, Decimal, str]]] = {
    SIGNAL_BTC: [
        (
            ID_BTC_STRATEGY,
            Decimal("0.15"),
            Decimal("5"),
            "Institutional accumulation narrative supports trend continuation",
        ),
        (
            ID_BTC_YIELD,
            Decimal("0.10"),
            Decimal("3"),
            "Fundamental DeFi narrative adds medium-term bid support",
        ),
    ],
    SIGNAL_ETH: [
        (
            ID_ETH_DERIVATIVES,
            Decimal("0.12"),
            Decimal("4"),
            "Derivatives positioning narrative aligns with range breakout watch",
        ),
    ],
}

_NOW = datetime.utcnow()


def _base_signals() -> list[dict[str, Any]]:
    return [
        {
            "signal_id": str(SIGNAL_BTC),
            "dedup_key": str(SIGNAL_BTC),
            "asset_pair": {
                "symbol": "BTC/USDT",
                "base": "BTC",
                "quote": "USDT",
                "exchange": "binance",
            },
            "signal_class": "LONG_CANDIDATE",
            "side": "BUY",
            "confidence_score": "78",
            "confidence_band": "HIGH",
            "is_publishable": True,
            "generated_at": (_NOW - timedelta(minutes=4)).isoformat(),
            "expiry_at": (_NOW + timedelta(hours=4)).isoformat(),
            "regime": "TRENDING_UP",
            "thesis": (
                "Momentum + trend alignment: 4h close above 50 EMA, RSI 62, MACD bullish cross on 1h. "
                "Institutional BTC narratives add fundamental support."
            ),
            "narrative_summary": "Institutional BTC accumulation + native yield narrative",
            "invalidation_condition": "4h close below 50 EMA",
            "expected_holding_horizon": "4h",
            "entry_price": "67250.00",
            "target_price": "70100.00",
            "contributing_factors": [
                {
                    "feature_family": "trend",
                    "feature_name": "sma_50_distance",
                    "value": "0.012",
                    "weight": "0.25",
                    "direction": "bullish",
                    "description": "Price 1.2% above 50-period SMA on 4h",
                    "z_score": "1.4",
                    "source_type": "feature",
                },
                {
                    "feature_family": "momentum",
                    "feature_name": "rsi_14",
                    "value": "62",
                    "weight": "0.20",
                    "direction": "bullish",
                    "description": "RSI in bullish zone without overbought extreme",
                    "source_type": "feature",
                },
                {
                    "feature_family": "intelligence",
                    "feature_name": "research_grade_development",
                    "value": "0.85",
                    "weight": "0.15",
                    "direction": "bullish",
                    "description": "Institutional accumulation narrative supports trend continuation",
                    "source_type": "intelligence",
                    "intelligence_item_id": str(ID_BTC_STRATEGY),
                },
            ],
            "timeframe_alignment": {"1h": "bullish", "4h": "bullish", "1d": "neutral"},
            "freshness": {
                "market_data_age_seconds": 42,
                "feature_computed_age_seconds": 240,
                "signal_age_seconds": 240,
            },
            "provenance": {
                "data_sources": ["binance", "rss_fan_in"],
                "observation_window": "24h",
                "computation_version": "1.0.0",
                "rule_version": "v1.2.0",
                "generated_by": "signal-engine",
                "input_feature_count": 14,
                "computation_time_ms": 87,
                "intelligence_item_ids": [str(ID_BTC_STRATEGY), str(ID_BTC_YIELD)],
            },
            "changes_since_previous": {
                "previous_signal_id": "990e8400-e29b-41d4-a716-446655440000",
                "confidence_delta": "6",
                "summary": "RSI crossed 60; new 4h bar confirmed trend",
            },
            "beginner_summary": {
                "headline": "Research suggests upward bias for BTC over the next few hours.",
                "risk_note": (
                    "Paper research only. Not financial advice. Signal can fail if price closes below support."
                ),
                "confidence_plain": "Fairly strong agreement across indicators, but not guaranteed.",
            },
            "status": "ACTIVE",
            "schema_version": "1.0.0",
        },
        {
            "signal_id": str(SIGNAL_ETH),
            "asset_pair": {
                "symbol": "ETH/USDT",
                "base": "ETH",
                "quote": "USDT",
                "exchange": "binance",
            },
            "signal_class": "WATCH",
            "side": "HOLD",
            "confidence_score": "58",
            "confidence_band": "MEDIUM",
            "is_publishable": False,
            "generated_at": (_NOW - timedelta(minutes=12)).isoformat(),
            "regime": "RANGING",
            "thesis": "Mixed momentum; waiting for breakout confirmation above range high.",
            "narrative_summary": "ETH derivatives positioning narrative",
            "invalidation_condition": "Close below range low on 4h",
            "expected_holding_horizon": "8h",
            "contributing_factors": [
                {
                    "feature_family": "intelligence",
                    "feature_name": "narrative_emerging",
                    "value": "0.85",
                    "weight": "0.12",
                    "direction": "neutral",
                    "description": "Derivatives positioning narrative aligns with range breakout watch",
                    "source_type": "intelligence",
                    "intelligence_item_id": str(ID_ETH_DERIVATIVES),
                },
            ],
            "provenance": {
                "data_sources": ["binance", "rss_fan_in"],
                "observation_window": "24h",
                "computation_version": "1.0.0",
                "rule_version": "v1.2.0",
                "generated_by": "signal-engine",
                "input_feature_count": 12,
                "intelligence_item_ids": [str(ID_ETH_DERIVATIVES)],
            },
            "status": "ACTIVE",
        },
    ]


class SignalCatalog:
    """Build signal responses with linked intelligence from cache."""

    def __init__(self, cache: IntelligenceCache | None = None) -> None:
        self._cache = cache or get_intelligence_cache()

    async def _resolve_links(self, signal_id: UUID, generated_at: datetime) -> list[dict[str, Any]]:
        links = SIGNAL_INTELLIGENCE_LINKS.get(signal_id, [])
        resolved: list[dict[str, Any]] = []
        for intel_id, weight, delta, snippet in links:
            item = await self._cache.get_item(intel_id)
            if item is None:
                item = SEED_INTELLIGENCE_BY_ID.get(intel_id)
            if item is None:
                continue
            if item.observed_at > generated_at:
                continue
            resolved.append(
                {
                    "intelligence_id": str(intel_id),
                    "contribution_weight": str(weight),
                    "confidence_delta": str(delta),
                    "explain_snippet": snippet,
                    "item": intelligence_from_domain(item).model_dump(mode="json"),
                }
            )
        resolved.sort(
            key=lambda x: (Decimal(x["contribution_weight"]), x["item"]["observed_at"]),
            reverse=True,
        )
        return resolved

    async def list_signals(self, *, publishable_only: bool = False) -> list[SignalSchema]:
        signals: list[SignalSchema] = []
        for raw in _base_signals():
            if publishable_only and not raw.get("is_publishable"):
                continue
            generated_at = datetime.fromisoformat(str(raw["generated_at"]).replace("Z", "+00:00"))
            if generated_at.tzinfo:
                generated_at = generated_at.replace(tzinfo=None)
            signal_id = UUID(str(raw["signal_id"]))
            raw["linked_intelligence"] = await self._resolve_links(signal_id, generated_at)
            signals.append(signal_to_schema(raw))
        return signals

    async def get_signal(self, signal_id: UUID) -> SignalSchema | None:
        for raw in _base_signals():
            if UUID(str(raw["signal_id"])) != signal_id:
                continue
            generated_at = datetime.fromisoformat(str(raw["generated_at"]).replace("Z", "+00:00"))
            if generated_at.tzinfo:
                generated_at = generated_at.replace(tzinfo=None)
            raw["linked_intelligence"] = await self._resolve_links(signal_id, generated_at)
            return signal_to_schema(raw)
        return None

    async def signals_for_intelligence(self, intelligence_id: UUID) -> list[UUID]:
        matched: list[UUID] = []
        for signal_id, links in SIGNAL_INTELLIGENCE_LINKS.items():
            if any(link[0] == intelligence_id for link in links):
                matched.append(signal_id)
        return matched



class _CatalogHolder:
    instance: SignalCatalog | None = None


def get_signal_catalog() -> SignalCatalog:
    if _CatalogHolder.instance is None:
        _CatalogHolder.instance = SignalCatalog()
    return _CatalogHolder.instance
