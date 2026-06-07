"""Seed intelligence items aligned with dashboard mock data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from signals_lab.domain.intelligence import IntelligenceItem, SignalContribution
from signals_lab.domain.intelligence_enums import ContentRole, IntelligenceSourceType, ProviderTier

_NOW = datetime.utcnow()

# Fixed UUIDs shared with apps/web mock fixtures
ID_BTC_STRATEGY = UUID("f1111111-1111-4111-8111-111111111111")
ID_BTC_YIELD = UUID("f2222222-2222-4222-8222-222222222222")
ID_ETH_DERIVATIVES = UUID("f3333333-3333-4333-8333-333333333333")
ID_ETH_ETF = UUID("f4444444-4444-4444-8444-444444444444")
ID_VENEZUELA_STABLE = UUID("f5555555-5555-4555-8555-555555555555")
ID_DEPIN_GAMING = UUID("f6666666-6666-4666-8666-666666666666")


@dataclass(frozen=True)
class _SeedSpec:
    item_id: UUID
    title: str
    source: str
    assets: list[str]
    hours_ago: float = 2
    credibility: str = "0.85"
    confirmation: int = 1
    providers: tuple[str, ...] = ("rss_fan_in",)
    contribution: SignalContribution | None = None
    body: str = ""


def _item(spec: _SeedSpec) -> IntelligenceItem:
    provider_list = list(spec.providers)
    return IntelligenceItem(
        id=spec.item_id,
        external_id=f"seed:{spec.item_id}",
        dedup_key=f"title:seed-{spec.item_id.hex[:8]}",
        observed_at=_NOW - timedelta(hours=spec.hours_ago),
        ingested_at=_NOW,
        provider=provider_list[0],
        provider_tier=ProviderTier.A,
        source_type=IntelligenceSourceType.NEWS,
        original_source=spec.source,
        content_role=ContentRole.PRIMARY,
        title=spec.title,
        body=spec.body or spec.title,
        asset_tags=spec.assets,
        credibility_score=Decimal(spec.credibility),
        novelty_score=Decimal("0.72"),
        cross_source_confirmation_count=spec.confirmation,
        confirming_providers=provider_list,
        signal_contribution=spec.contribution,
    )


SEED_INTELLIGENCE_ITEMS: list[IntelligenceItem] = [
    _item(
        _SeedSpec(
            item_id=ID_BTC_STRATEGY,
            title="The Strategy playbook looks different in 2026",
            source="Blockworks",
            assets=["BTC"],
            hours_ago=3,
            contribution=SignalContribution(
                narrative_class="research_grade_development",
                weight=Decimal("0.15"),
                confidence_delta=Decimal("5"),
                explain_snippet="Institutional accumulation narrative supports trend continuation",
            ),
        )
    ),
    _item(
        _SeedSpec(
            item_id=ID_BTC_YIELD,
            title="Yield Basis is making native BTC yield a reality",
            source="Blockworks",
            assets=["BTC"],
            hours_ago=5,
            contribution=SignalContribution(
                narrative_class="research_grade_development",
                weight=Decimal("0.10"),
                confidence_delta=Decimal("3"),
                explain_snippet="Fundamental DeFi narrative adds medium-term bid support",
            ),
        )
    ),
    _item(
        _SeedSpec(
            item_id=ID_ETH_DERIVATIVES,
            title="ETH derivatives reset and the next retail trade",
            source="Blockworks",
            assets=["ETH"],
            hours_ago=4,
            contribution=SignalContribution(
                narrative_class="narrative_emerging",
                weight=Decimal("0.12"),
                confidence_delta=Decimal("4"),
                explain_snippet="Derivatives positioning narrative aligns with range breakout watch",
            ),
        )
    ),
    _item(
        _SeedSpec(
            item_id=ID_ETH_ETF,
            title="Spot ETH ETF sees record inflows",
            source="The Block",
            assets=["ETH", "BTC"],
            hours_ago=2,
            confirmation=4,
            providers=("rss_fan_in", "rss_coindesk", "rss_cointelegraph", "rss_blockworks"),
            contribution=SignalContribution(
                narrative_class="market_confirmed_breakout_catalyst",
                weight=Decimal("0.22"),
                confidence_delta=Decimal("8"),
                explain_snippet="ETF inflows confirmed by 4 independent sources",
            ),
        )
    ),
    _item(
        _SeedSpec(
            item_id=ID_VENEZUELA_STABLE,
            title="Venezuela's sanctions are stablecoins' proof of concept",
            source="Blockworks",
            assets=[],
            hours_ago=1.5,
        )
    ),
    _item(
        _SeedSpec(
            item_id=ID_DEPIN_GAMING,
            title="DePIN and crypto gaming led a surprising end-of-year rebound",
            source="Blockworks",
            assets=["BTC"],
            hours_ago=6,
        )
    ),
]

SEED_INTELLIGENCE_BY_ID: dict[UUID, IntelligenceItem] = {i.id: i for i in SEED_INTELLIGENCE_ITEMS}
