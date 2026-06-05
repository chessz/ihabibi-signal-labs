"""
Social/Sentiment domain models for signals-lab
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from .enums import ObservationType


class SocialObservation(BaseModel):
    """Raw social/sentiment data observation (time-series)"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    asset_pair: "AssetPair"  # Forward reference
    timestamp: datetime
    mention_count: int = Field(..., ge=0, description="Total mentions in period")
    sentiment_score: Decimal = Field(
        ..., 
        ge=-1, 
        le=1, 
        description="Overall sentiment score (-1 to 1)"
    )
    sentiment_positive: int = Field(default=0, ge=0)
    sentiment_negative: int = Field(default=0, ge=0)
    sentiment_neutral: int = Field(default=0, ge=0)
    influencer_mentions: int = Field(default=0, ge=0, description="Mentions from known influencers")
    social_dominance_pct: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        description="% of total crypto mentions for this asset"
    )
    topic_tags: List[str] = Field(default_factory=list, description="Detected topics/narratives")
    source: str = Field(..., description="Data provider identifier")
    
    # Computed properties
    @property
    def total_sentiment_mentions(self) -> int:
        return self.sentiment_positive + self.sentiment_negative + self.sentiment_neutral
    
    @property
    def positive_ratio(self) -> Decimal:
        total = self.total_sentiment_mentions
        if total == 0:
            return Decimal("0")
        return Decimal(self.sentiment_positive) / total
    
    @property
    def negative_ratio(self) -> Decimal:
        total = self.total_sentiment_mentions
        if total == 0:
            return Decimal("0")
        return Decimal(self.sentiment_negative) / total
    
    @property
    def sentiment_momentum(self) -> Decimal:
        """Simple momentum: positive - negative ratio"""
        return self.positive_ratio - self.negative_ratio
    
    @property
    def observation_type(self) -> ObservationType:
        return ObservationType.SOCIAL


class SocialMetrics(BaseModel):
    """Aggregated social metrics over a window"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    asset_pair: "AssetPair"
    window_start: datetime
    window_end: datetime
    total_mentions: int
    avg_sentiment: Decimal
    sentiment_volatility: Decimal
    mention_velocity: Decimal = Field(description="Mentions per hour")
    velocity_change_pct: Optional[Decimal] = None
    dominance_avg: Decimal
    dominance_change_pct: Optional[Decimal] = None
    influencer_mention_ratio: Decimal
    topic_distribution: dict = Field(default_factory=dict)
    source: str


class InfluencerObservation(BaseModel):
    """Individual influencer mention"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    asset_pair: "AssetPair"
    timestamp: datetime
    influencer_id: str
    influencer_name: str
    platform: str  # twitter, youtube, reddit, etc.
    follower_count: int
    mention_text: str
    sentiment_score: Decimal
    engagement: int = Field(default=0, description="Likes + retweets + replies")
    url: Optional[str] = None
    source: str


class NarrativeCluster(BaseModel):
    """Detected narrative/topic cluster"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    cluster_id: str
    name: str
    keywords: List[str]
    assets: List[str] = Field(description="Assets mentioned in this narrative")
    mention_count: int
    avg_sentiment: Decimal
    growth_rate: Decimal = Field(description="Week-over-week growth")
    first_seen: datetime
    last_seen: datetime
    is_emerging: bool = False


# Forward reference resolution
from .market import AssetPair
SocialObservation.model_rebuild()
SocialMetrics.model_rebuild()
InfluencerObservation.model_rebuild()