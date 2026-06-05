"""
Domain Enums for signals-lab
"""
from enum import Enum


class SignalClass(str, Enum):
    """Signal output classes"""
    LONG_CANDIDATE = "long_candidate"
    SHORT_CANDIDATE = "short_candidate"
    WATCH_ONLY = "watch_only"
    IGNORE = "ignore"


class ConfidenceBand(str, Enum):
    """Confidence bands for signals"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class SignalSide(str, Enum):
    """Signal side/direction"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


class MarketRegime(str, Enum):
    """Market regime classification"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class DataSourceType(str, Enum):
    """Data source type categories"""
    MARKET = "market"
    ONCHAIN = "onchain"
    SOCIAL = "social"
    EVENTS = "events"


class SignalStatus(str, Enum):
    """Signal lifecycle status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    FILLED_PAPER = "filled_paper"
    CANCELLED = "cancelled"


class PositionStatus(str, Enum):
    """Paper position status"""
    OPEN = "open"
    CLOSED = "closed"
    STOPPED = "stopped"
    EXPIRED = "expired"
    LIQUIDATED = "liquidated"


class ObservationType(str, Enum):
    """Types of observations for storage routing"""
    MARKET = "market"
    SOCIAL = "social"
    ONCHAIN = "onchain"
    EVENTS = "events"
    FEATURES = "features"


class ProviderStatus(str, Enum):
    """Data provider health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


class WorkerStatus(str, Enum):
    """Background worker status"""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class EventSeverity(int, Enum):
    """Event severity levels (1-5)"""
    LOW = 1
    MEDIUM_LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class EventType(str, Enum):
    """Event type categories"""
    REGULATORY = "regulatory"
    ETF = "etf"
    EXCHANGE_INCIDENT = "exchange_incident"
    GEOPOLITICAL = "geopolitical"
    MACRO = "macro"
    TECHNICAL = "technical"
    CORPORATE = "corporate"
    UNKNOWN = "unknown"


class FeatureFamily(str, Enum):
    """Feature family categories"""
    TREND = "trend"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    SOCIAL = "social"
    ONCHAIN = "onchain"
    EVENTS = "events"
    CROSS_ASSET = "cross_asset"


class InvalidationReason(str, Enum):
    """Signal invalidation reasons"""
    STOP_LOSS_HIT = "stop_loss_hit"
    TAKE_PROFIT_HIT = "take_profit_hit"
    TIME_EXPIRY = "time_expiry"
    REGIME_CHANGE = "regime_change"
    CONFIDENCE_DROPPED = "confidence_dropped"
    NEW_CONTRADICTING_SIGNAL = "new_contradicting_signal"
    MANUAL_CANCEL = "manual_cancel"


class ExitReason(str, Enum):
    """Position exit reasons"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TIME_BASED = "time_based"
    SIGNAL_REVERSAL = "signal_reversal"
    REGIME_CHANGE = "regime_change"
    MANUAL = "manual"
    EXPIRED = "expired"