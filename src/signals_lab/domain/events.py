"""
Event/Geopolitical domain models for signals-lab
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict

from .enums import ObservationType, EventType, EventSeverity

if TYPE_CHECKING:
    from .market import AssetPair


class EventObservation(BaseModel):
    """News/event/geopolitical data observation (time-series)"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    timestamp: datetime
    event_type: str = Field(
        ...,
        description="regulatory, etf, exchange_incident, geopolitical, macro, technical, corporate"
    )
    title: str
    description: str
    severity: int = Field(default=1, ge=1, le=5, description="Severity 1-5")
    affected_assets: List[str] = Field(default_factory=list)
    region: Optional[str] = Field(default=None, description="Geographic region")
    country: Optional[str] = None
    country_sentiment: Optional[Decimal] = Field(
        default=None, ge=-1, le=1, description="Country-level sentiment"
    )
    market_impact_estimate: Optional[Decimal] = Field(
        default=None, ge=0, le=1, description="Estimated market impact 0-1"
    )
    tags: List[str] = Field(default_factory=list)
    source: str = Field(..., description="Data provider identifier")
    url: Optional[str] = None
    is_breaking: bool = Field(default=False, description="Breaking news flag")
    confidence: Optional[Decimal] = Field(
        default=None, ge=0, le=1, description="Source confidence 0-1"
    )

    @property
    def observation_type(self) -> ObservationType:
        return ObservationType.EVENTS

    @property
    def severity_label(self) -> str:
        labels = {1: "low", 2: "medium-low", 3: "medium", 4: "high", 5: "critical"}
        return labels.get(self.severity, "unknown")


class EventImpactScore(BaseModel):
    """Computed event impact score for a specific asset"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset_pair: "AssetPair"
    event: EventObservation
    impact_score: Decimal = Field(..., ge=0, le=1)
    relevance_score: Decimal = Field(..., ge=0, le=1, description="How relevant to asset")
    decay_factor: Decimal = Field(..., ge=0, le=1, description="Time decay multiplier")
    risk_penalty: Decimal = Field(..., ge=0, description="Risk penalty for signals")
    catalyst_proximity_hours: Optional[Decimal] = None
    estimated_duration_hours: Optional[Decimal] = None
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class RegulatoryEvent(BaseModel):
    """Regulatory-specific event"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    event: EventObservation
    regulator_name: str
    jurisdiction: str
    action_type: str  # e.g., "lawsuit", "approval", "guidance", "ban"
    affected_entities: List[str] = Field(default_factory=list)
    penalty_amount_usd: Optional[Decimal] = None
    effective_date: Optional[datetime] = None
    compliance_deadline: Optional[datetime] = None


class GeoPoliticalRisk(BaseModel):
    """Geopolitical risk assessment"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    event: EventObservation
    risk_level: int = Field(..., ge=1, le=5)
    affected_regions: List[str]
    energy_impact: Optional[Decimal] = Field(default=None, ge=0, le=1)
    trade_impact: Optional[Decimal] = Field(default=None, ge=0, le=1)
    financial_system_impact: Optional[Decimal] = Field(default=None, ge=0, le=1)
    safe_haven_flow_estimate: Optional[Decimal] = None
    risk_premium_bps: Optional[int] = None


class EventWindow(BaseModel):
    """Window of events for analysis"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset_pair: "AssetPair"
    window_start: datetime
    window_end: datetime
    events: List[EventObservation]
    total_events: int
    avg_severity: Decimal
    max_severity: int
    cumulative_impact: Decimal
    risk_penalty_total: Decimal
    catalyst_score: Decimal = Field(description="Positive catalyst potential")
    risk_score: Decimal = Field(description="Risk/drag potential")
    region_distribution: dict = Field(default_factory=dict)
    type_distribution: dict = Field(default_factory=dict)