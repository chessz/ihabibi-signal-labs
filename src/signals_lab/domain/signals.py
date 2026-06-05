"""
Signal generation domain models for signals-lab
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict

from .enums import (
    SignalClass, ConfidenceBand, SignalSide, MarketRegime,
    SignalStatus, InvalidationReason
)

if TYPE_CHECKING:
    from .market import AssetPair


class ContributingFactor(BaseModel):
    """A single factor contributing to a signal's generation"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    feature_family: str
    feature_name: str
    value: Decimal
    weight: Decimal = Field(..., ge=0, le=1, description="Contribution weight to confidence")
    direction: str = Field(..., description="bullish, bearish, neutral")
    description: str
    z_score: Optional[Decimal] = None


class StopLogic(BaseModel):
    """Suggested stop-loss logic"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: str = Field(..., description="fixed_pct, atr_trailing, structure")
    value: Decimal
    reference_price: Decimal


class SellLogic(BaseModel):
    """Suggested take-profit/sell logic"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: str = Field(
        ..., description="take_profit_pct, trailing, time_based, signal_reversal"
    )
    value: Decimal
    reference_price: Decimal


class ProvenanceRecord(BaseModel):
    """Data lineage and provenance for a signal"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data_sources: List[str] = Field(default_factory=list)
    observation_window: str = Field(default="24h")
    computation_version: str = "1.0.0"
    rule_version: str = "v1.0.0"
    generated_by: str = Field(default="signal-engine")
    input_feature_count: int = 0
    computation_time_ms: Optional[int] = None


class Signal(BaseModel):
    """
    Core signal entity - the primary output of the signal engine.
    
    Each signal represents a research-grade trading idea with full
    explainability and provenance tracking.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    signal_id: UUID = Field(default_factory=uuid4)
    asset_pair: "AssetPair"
    signal_class: SignalClass
    side: SignalSide
    confidence_score: Decimal = Field(..., ge=0, le=100)
    confidence_band: ConfidenceBand
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expiry_at: Optional[datetime] = None
    regime: MarketRegime = MarketRegime.UNKNOWN
    thesis: str = Field(
        ..., min_length=10, description="Human-readable explanation of the signal"
    )
    contributing_factors: List[ContributingFactor] = Field(default_factory=list)
    invalidation_condition: str = Field(
        ..., min_length=5, description="What would make this signal invalid"
    )
    suggested_stop: Optional[StopLogic] = None
    suggested_sell: Optional[SellLogic] = None
    expected_holding_horizon: str = Field(
        default="4h", description="Expected holding period"
    )
    provenance: ProvenanceRecord = Field(default_factory=ProvenanceRecord)
    status: SignalStatus = SignalStatus.ACTIVE
    entry_price: Optional[Decimal] = None
    target_price: Optional[Decimal] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Computed properties
    @property
    def is_publishable(self) -> bool:
        """Only high/extreme confidence signals are eligible for publishing"""
        return self.confidence_band in (ConfidenceBand.HIGH, ConfidenceBand.EXTREME)

    @property
    def is_active(self) -> bool:
        return self.status == SignalStatus.ACTIVE

    @property
    def is_expired(self) -> bool:
        if self.expiry_at:
            return datetime.utcnow() > self.expiry_at
        return False

    @property
    def primary_direction(self) -> str:
        """Net direction from contributing factors"""
        bullish_count = sum(1 for f in self.contributing_factors if f.direction == "bullish")
        bearish_count = sum(1 for f in self.contributing_factors if f.direction == "bearish")
        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        return "neutral"


class SignalRule(BaseModel):
    """Configurable signal generation rule"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    rule_id: str = Field(..., description="Unique rule identifier")
    name: str
    description: str
    version: str
    signal_class: SignalClass
    conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Rule conditions referencing features and thresholds"
    )
    required_features: List[str] = Field(default_factory=list)
    min_confidence: Decimal = Field(default=Decimal("60"), ge=0, le=100)
    weight: Decimal = Field(default=Decimal("1.0"), ge=0)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    cooldown_hours: int = Field(default=4, ge=0)


class SignalCandidate(BaseModel):
    """Intermediate signal candidate before final ranking"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset_pair: "AssetPair"
    rule_id: str
    signal_class: SignalClass
    side: SignalSide
    raw_score: Decimal = Field(..., ge=0, le=100)
    contributing_factors: List[ContributingFactor] = Field(default_factory=list)
    regime: MarketRegime = MarketRegime.UNKNOWN
    thesis_template: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SignalOutputBatch(BaseModel):
    """Batch of signals produced in one generation run"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    signals: List[Signal] = Field(default_factory=list)
    candidates_evaluated: int = 0
    signals_generated: int = 0
    publishable_signals: int = 0
    computation_time_ms: Optional[int] = None
    rule_version: str = "v1.0.0"
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def by_confidence_band(self) -> Dict[ConfidenceBand, List[Signal]]:
        result: Dict[ConfidenceBand, List[Signal]] = {b: [] for b in ConfidenceBand}
        for s in self.signals:
            result[s.confidence_band].append(s)
        return result

    @property
    def publishable(self) -> List[Signal]:
        return [s for s in self.signals if s.is_publishable]