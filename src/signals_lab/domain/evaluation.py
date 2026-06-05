"""
Paper trading evaluation domain models for signals-lab
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict

from .enums import (
    SignalClass, ConfidenceBand, SignalSide, MarketRegime,
    PositionStatus, ExitReason
)

if TYPE_CHECKING:
    from .market import AssetPair


class PaperPosition(BaseModel):
    """Simulated paper-trading position for evaluation"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    position_id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    asset_pair: "AssetPair"
    side: SignalSide
    entry_price: Decimal
    entry_time: datetime
    quantity: Decimal = Field(..., gt=0)
    notional_usd: Decimal = Field(..., ge=0)
    stop_price: Optional[Decimal] = None
    target_price: Optional[Decimal] = None
    status: PositionStatus = PositionStatus.OPEN
    exit_price: Optional[Decimal] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    pnl_usd: Optional[Decimal] = None
    pnl_pct: Optional[Decimal] = None
    fees_usd: Decimal = Field(default=Decimal("0"), ge=0)
    slippage_usd: Decimal = Field(default=Decimal("0"), ge=0)
    max_favorable_excursion_pct: Optional[Decimal] = None
    max_adverse_excursion_pct: Optional[Decimal] = None
    holding_period_hours: Optional[Decimal] = None
    is_win: Optional[bool] = None
    signal_confidence_band: Optional[ConfidenceBand] = None
    signal_regime: Optional[MarketRegime] = None
    signal_class: Optional[SignalClass] = None
    tags: Dict[str, Any] = Field(default_factory=dict)

    @property
    def net_pnl_usd(self) -> Optional[Decimal]:
        """PnL after fees and slippage"""
        if self.pnl_usd is not None:
            return self.pnl_usd - self.fees_usd - self.slippage_usd
        return None

    @property
    def r_multiple(self) -> Optional[Decimal]:
        """Risk multiple: PnL / risk"""
        if self.entry_price and self.stop_price and self.pnl_usd and self.entry_price != self.stop_price:
            risk_per_unit = abs(self.entry_price - self.stop_price)
            if risk_per_unit > 0:
                return self.pnl_usd / (risk_per_unit * self.quantity)
        return None

    @property
    def is_closed(self) -> bool:
        return self.status in (PositionStatus.CLOSED, PositionStatus.STOPPED,
                               PositionStatus.EXPIRED, PositionStatus.LIQUIDATED)


class EvaluationMetrics(BaseModel):
    """Aggregated evaluation metrics for a period"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    period_start: datetime
    period_end: datetime
    total_signals: int = 0
    total_positions: int = 0
    closed_positions: int = 0
    open_positions: int = 0
    winning_positions: int = 0
    losing_positions: int = 0
    win_rate: Decimal = Decimal("0")
    loss_rate: Decimal = Decimal("0")
    expectancy: Decimal = Decimal("0")
    avg_return_pct: Decimal = Decimal("0")
    median_return_pct: Optional[Decimal] = None
    max_return_pct: Optional[Decimal] = None
    min_return_pct: Optional[Decimal] = None
    std_return_pct: Optional[Decimal] = None
    max_drawdown_pct: Decimal = Decimal("0")
    profit_factor: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    sortino_ratio: Optional[Decimal] = None
    calmar_ratio: Optional[Decimal] = None
    total_pnl_usd: Decimal = Decimal("0")
    total_fees_usd: Decimal = Decimal("0")
    total_slippage_usd: Decimal = Decimal("0")
    avg_holding_hours: Optional[Decimal] = None
    avg_r_multiple: Optional[Decimal] = None

    # Breakdown by confidence band
    hit_rate_by_confidence: Dict[str, Decimal] = Field(default_factory=dict)
    avg_return_by_confidence: Dict[str, Decimal] = Field(default_factory=dict)
    win_rate_by_confidence: Dict[str, Decimal] = Field(default_factory=dict)

    # Breakdown by regime
    hit_rate_by_regime: Dict[str, Decimal] = Field(default_factory=dict)
    avg_return_by_regime: Dict[str, Decimal] = Field(default_factory=dict)

    # Breakdown by signal class
    hit_rate_by_signal_class: Dict[str, Decimal] = Field(default_factory=dict)
    avg_return_by_signal_class: Dict[str, Decimal] = Field(default_factory=dict)

    # Signal quality metrics
    signal_decay_half_life_hours: Optional[Decimal] = None
    sell_timing_quality_score: Optional[Decimal] = None
    avg_max_favorable_excursion_pct: Optional[Decimal] = None
    avg_max_adverse_excursion_pct: Optional[Decimal] = None


class DecayAnalysis(BaseModel):
    """Signal performance decay analysis"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    signal_id: UUID
    time_buckets_hours: List[int] = Field(default_factory=list)
    hit_rate_by_bucket: Dict[int, Decimal] = Field(default_factory=dict)
    avg_return_by_bucket: Dict[int, Decimal] = Field(default_factory=dict)
    half_life_hours: Optional[Decimal] = None
    r_squared: Optional[Decimal] = None
    decay_model: str = "exponential"


class SellTimingMetrics(BaseModel):
    """Sell timing quality analysis"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    position_id: UUID
    exit_reason: ExitReason
    exit_price: Decimal
    peak_price_after_entry: Decimal
    trough_price_after_entry: Decimal
    exit_vs_peak_pct: Decimal = Field(
        description="How far below peak the exit was"
    )
    exit_vs_trough_pct: Decimal = Field(
        description="How far above trough the exit was"
    )
    optimal_exit_price: Optional[Decimal] = None
    exit_efficiency_pct: Optional[Decimal] = Field(
        default=None, description="How close to optimal exit (0-100)"
    )
    held_too_long: bool = False
    exited_too_early: bool = False


class EvaluationReport(BaseModel):
    """Full evaluation report for a period"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    report_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    period_start: datetime
    period_end: datetime
    metrics: EvaluationMetrics
    decay_analysis: List[DecayAnalysis] = Field(default_factory=list)
    sell_timing: List[SellTimingMetrics] = Field(default_factory=list)
    confidence_band_comparison: Dict[str, Any] = Field(default_factory=dict)
    source_attribution: Dict[str, Any] = Field(default_factory=dict)
    regime_analysis: Dict[str, Any] = Field(default_factory=dict)
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)