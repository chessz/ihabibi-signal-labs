"""Signal API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from signals_lab.api.schemas.intelligence import LinkedIntelligenceSchema


class AssetPairSchema(BaseModel):
    symbol: str
    base: str
    quote: str
    exchange: str


class ContributingFactorSchema(BaseModel):
    feature_family: str
    feature_name: str
    value: Decimal
    weight: Decimal
    direction: str
    description: str
    z_score: Decimal | None = None
    source_type: str = "feature"
    intelligence_item_id: UUID | None = None


class ProvenanceSchema(BaseModel):
    data_sources: list[str] = Field(default_factory=list)
    observation_window: str = "24h"
    computation_version: str = "1.0.0"
    rule_version: str = "v1.0.0"
    generated_by: str = "signal-engine"
    input_feature_count: int = 0
    computation_time_ms: int | None = None
    intelligence_item_ids: list[UUID] = Field(default_factory=list)


class FreshnessSchema(BaseModel):
    market_data_age_seconds: int
    feature_computed_age_seconds: int
    signal_age_seconds: int


class BeginnerSummarySchema(BaseModel):
    headline: str
    risk_note: str
    confidence_plain: str


class ChangesSincePreviousSchema(BaseModel):
    previous_signal_id: UUID
    confidence_delta: Decimal
    summary: str


class SignalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    signal_id: UUID
    dedup_key: UUID | None = None
    asset_pair: AssetPairSchema
    signal_class: str
    side: str
    confidence_score: Decimal
    confidence_band: str
    is_publishable: bool
    generated_at: datetime
    expiry_at: datetime | None = None
    regime: str
    thesis: str
    invalidation_condition: str
    expected_holding_horizon: str = "4h"
    entry_price: Decimal | None = None
    target_price: Decimal | None = None
    contributing_factors: list[ContributingFactorSchema] = Field(default_factory=list)
    timeframe_alignment: dict[str, str] | None = None
    freshness: FreshnessSchema | None = None
    provenance: ProvenanceSchema = Field(default_factory=ProvenanceSchema)
    changes_since_previous: ChangesSincePreviousSchema | None = None
    beginner_summary: BeginnerSummarySchema | None = None
    status: str = "ACTIVE"
    schema_version: str = "1.0.0"
    narrative_summary: str | None = None
    linked_intelligence: list[LinkedIntelligenceSchema] = Field(default_factory=list)


class SignalListResponse(BaseModel):
    schema_version: str = "1.0.0"
    generated_at: datetime
    total: int
    items: list[SignalSchema]


def signal_to_schema(data: dict[str, Any]) -> SignalSchema:
    return SignalSchema.model_validate(data)
