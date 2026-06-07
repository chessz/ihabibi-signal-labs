"""Intelligence API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SignalContributionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    narrative_class: str
    weight: Decimal
    confidence_delta: Decimal
    explain_snippet: str


class IntelligenceItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str
    dedup_key: str
    observed_at: datetime
    ingested_at: datetime
    provider: str
    provider_tier: str
    source_type: str
    original_source: str
    content_role: str
    url: str | None = None
    title: str
    body: str = ""
    language: str = "en"
    asset_tags: list[str] = Field(default_factory=list)
    entity_tags: list[str] = Field(default_factory=list)
    sentiment_score: Decimal | None = None
    credibility_score: Decimal
    novelty_score: Decimal
    cross_source_confirmation_count: int = 1
    confirming_providers: list[str] = Field(default_factory=list)
    narrative_cluster_id: str | None = None
    signal_contribution: SignalContributionSchema | None = None


class LinkedIntelligenceSchema(BaseModel):
    intelligence_id: UUID
    contribution_weight: Decimal
    confidence_delta: Decimal
    explain_snippet: str
    item: IntelligenceItemSchema


class IntelligenceTickerResponse(BaseModel):
    schema_version: str = "1.0.0"
    generated_at: datetime
    items: list[IntelligenceItemSchema]


class IntelligenceFeedResponse(BaseModel):
    schema_version: str = "1.0.0"
    generated_at: datetime
    total: int
    items: list[IntelligenceItemSchema]


class IntelligenceSignalsResponse(BaseModel):
    schema_version: str = "1.0.0"
    intelligence_id: UUID
    signal_ids: list[UUID]


def intelligence_from_domain(item: Any) -> IntelligenceItemSchema:
    """Map domain IntelligenceItem to API schema."""
    payload = item.model_dump(mode="json")
    return IntelligenceItemSchema.model_validate(payload)
