"""
signals-lab: High-performance crypto signal research platform.

Research, feature generation, signal testing, paper evaluation, and API publishing
for crypto market signals consumed by iHabibi Trading.
"""
__version__ = "0.1.0"

from .domain.enums import (
    SignalClass, ConfidenceBand, SignalSide, MarketRegime,
    DataSourceType, SignalStatus, PositionStatus, ObservationType,
    ProviderStatus, WorkerStatus, EventSeverity, EventType,
    FeatureFamily, InvalidationReason, ExitReason,
)
from .domain.market import AssetPair, MarketObservation, Candle
from .domain.social import SocialObservation
from .domain.onchain import OnChainObservation
from .domain.events import EventObservation
from .domain.features import FeatureVector
from .domain.signals import Signal, ContributingFactor, ProvenanceRecord, StopLogic, SellLogic
from .domain.evaluation import PaperPosition, EvaluationMetrics, EvaluationReport

__all__ = [
    "__version__",
    "SignalClass", "ConfidenceBand", "SignalSide", "MarketRegime",
    "DataSourceType", "SignalStatus", "PositionStatus", "ObservationType",
    "ProviderStatus", "WorkerStatus", "EventSeverity", "EventType",
    "FeatureFamily", "InvalidationReason", "ExitReason",
    "AssetPair", "MarketObservation", "Candle",
    "SocialObservation", "OnChainObservation", "EventObservation",
    "FeatureVector", "Signal", "ContributingFactor", "ProvenanceRecord",
    "StopLogic", "SellLogic", "PaperPosition", "EvaluationMetrics",
    "EvaluationReport",
]