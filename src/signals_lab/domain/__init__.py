"""
Domain models for signals-lab.
"""

from .enums import (
    SignalClass,
    ConfidenceBand,
    SignalSide,
    MarketRegime,
    DataSourceType,
    SignalStatus,
    PositionStatus,
    ObservationType,
    ProviderStatus,
    WorkerStatus,
    EventSeverity,
    EventType,
    FeatureFamily,
    InvalidationReason,
    ExitReason,
)
from .market import (
    AssetPair,
    MarketObservation,
    Candle,
    OrderBookSnapshot,
    FundingRateObservation,
    OpenInterestObservation,
    MarketDataBatch,
)
from .social import (
    SocialObservation,
    SocialMetrics,
    InfluencerObservation,
    NarrativeCluster,
)
from .onchain import (
    OnChainObservation,
    WhaleTransaction,
    OnChainMetrics,
)
from .events import (
    EventObservation,
    EventImpactScore,
    RegulatoryEvent,
    GeoPoliticalRisk,
    EventWindow,
)
from .features import (
    FeatureDefinition,
    FeatureVector,
    FeatureBatch,
    FeatureRegistryEntry,
)
from .signals import (
    ContributingFactor,
    StopLogic,
    SellLogic,
    ProvenanceRecord,
    Signal,
    SignalRule,
    SignalCandidate,
    SignalOutputBatch,
)
from .evaluation import (
    PaperPosition,
    EvaluationMetrics,
    DecayAnalysis,
    SellTimingMetrics,
    EvaluationReport,
)

__all__ = [
    # Enums
    "SignalClass",
    "ConfidenceBand",
    "SignalSide",
    "MarketRegime",
    "DataSourceType",
    "SignalStatus",
    "PositionStatus",
    "ObservationType",
    "ProviderStatus",
    "WorkerStatus",
    "EventSeverity",
    "EventType",
    "FeatureFamily",
    "InvalidationReason",
    "ExitReason",
    # Market
    "AssetPair",
    "MarketObservation",
    "Candle",
    "OrderBookSnapshot",
    "FundingRateObservation",
    "OpenInterestObservation",
    "MarketDataBatch",
    # Social
    "SocialObservation",
    "SocialMetrics",
    "InfluencerObservation",
    "NarrativeCluster",
    # Onchain
    "OnChainObservation",
    "WhaleTransaction",
    "OnChainMetrics",
    # Events
    "EventObservation",
    "EventImpactScore",
    "RegulatoryEvent",
    "GeoPoliticalRisk",
    "EventWindow",
    # Features
    "FeatureDefinition",
    "FeatureVector",
    "FeatureBatch",
    "FeatureRegistryEntry",
    # Signals
    "ContributingFactor",
    "StopLogic",
    "SellLogic",
    "ProvenanceRecord",
    "Signal",
    "SignalRule",
    "SignalCandidate",
    "SignalOutputBatch",
    # Evaluation
    "PaperPosition",
    "EvaluationMetrics",
    "DecayAnalysis",
    "SellTimingMetrics",
    "EvaluationReport",
]