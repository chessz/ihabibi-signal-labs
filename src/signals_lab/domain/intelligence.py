"""Canonical intelligence domain models — pure Pydantic, no I/O."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .intelligence_enums import ContentRole, IntelligenceSourceType, ProviderTier


class RawIntelligenceRecord(BaseModel):
    """Provider-native record before normalization (ingestion boundary)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    external_id: str
    provider: str
    provider_tier: ProviderTier = ProviderTier.A
    source_type: IntelligenceSourceType
    original_source: str
    observed_at: datetime
    title: str
    body: str = ""
    url: str | None = None
    message_id: str | None = None
    language: str = "en"
    base_credibility: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)
    content_role: ContentRole = ContentRole.PRIMARY
    asset_hints: list[str] = Field(default_factory=list)
    entity_hints: list[str] = Field(default_factory=list)
    engagement_raw: int | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class SignalContribution(BaseModel):
    """Explainable contribution toward a future signal."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    narrative_class: str
    weight: Decimal = Field(..., ge=0, le=1)
    confidence_delta: Decimal
    explain_snippet: str


class IntelligenceItem(BaseModel):
    """Normalized intelligence unit for scoring, storage, and signal fusion."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID = Field(default_factory=uuid4)
    external_id: str
    dedup_key: str
    observed_at: datetime
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    provider: str
    provider_tier: ProviderTier
    source_type: IntelligenceSourceType
    original_source: str
    content_role: ContentRole

    url: str | None = None
    message_id: str | None = None

    title: str
    body: str = ""
    language: str = "en"
    translated_text: str | None = None

    asset_tags: list[str] = Field(default_factory=list)
    entity_tags: list[str] = Field(default_factory=list)

    sentiment_score: Decimal | None = Field(default=None, ge=-1, le=1)
    credibility_score: Decimal = Field(..., ge=0, le=1)
    novelty_score: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)
    engagement_score: Decimal | None = Field(default=None, ge=0, le=1)
    social_velocity: Decimal | None = None

    cross_source_confirmation_count: int = Field(default=1, ge=0)
    confirming_providers: list[str] = Field(default_factory=list)
    narrative_cluster_id: str | None = None

    signal_contribution: SignalContribution | None = None
    enrichment: dict[str, Any] = Field(default_factory=dict)

    # Storage / timeseries compatibility (no I/O here)
    @property
    def timestamp(self) -> datetime:
        return self.observed_at

    @property
    def source(self) -> str:
        return self.provider

    @property
    def symbol(self) -> str:
        return self.asset_tags[0] if self.asset_tags else "GLOBAL"

    @property
    def exchange(self) -> str:
        return "intelligence"

    def to_event_observation_fields(self) -> dict[str, Any]:
        """Map to legacy EventObservation-shaped fields for downstream stubs."""
        severity = 3
        high_confidence_sources = 3
        if (
            self.credibility_score >= Decimal("0.85")
            and self.cross_source_confirmation_count >= high_confidence_sources
        ):
            severity = 4
        if self.content_role == ContentRole.RUMOR:
            severity = 2
        return {
            "event_type": self.source_type.value,
            "title": self.title,
            "description": self.body or self.title,
            "severity": severity,
            "affected_assets": self.asset_tags,
            "tags": self.entity_tags,
            "source": self.provider,
            "url": self.url,
            "is_breaking": self.novelty_score >= Decimal("0.75"),
            "confidence": self.credibility_score,
        }
