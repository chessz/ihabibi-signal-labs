"""Intelligence pipeline enums."""

from __future__ import annotations

from enum import Enum


class ProviderTier(str, Enum):
    """Provider reliability tier — A must not block the pipeline."""

    A = "A"
    B = "B"
    C = "C"


class IntelligenceSourceType(str, Enum):
    """Canonical source category for intelligence items."""

    NEWS = "news"
    REDDIT = "reddit"
    X = "x"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    RESEARCH = "research"
    EXCHANGE = "exchange"
    PROTOCOL = "protocol"
    MARKET = "market"
    ONCHAIN = "onchain"
    INFLUENCER = "influencer"


class ContentRole(str, Enum):
    """Whether content is primary reporting or derivative."""

    PRIMARY = "primary"
    COMMENTARY = "commentary"
    REPOST = "repost"
    RUMOR = "rumor"


class NarrativeClass(str, Enum):
    """Narrative-aware signal classification (Stage 3 fusion)."""

    NARRATIVE_EMERGING = "narrative_emerging"
    SENTIMENT_SPIKE = "sentiment_spike"
    BREAKING_FUNDAMENTAL = "breaking_fundamental_event"
    CROWDING_OVERHEATED = "crowding_overheated_social"
    UNCONFIRMED_RUMOR = "unconfirmed_rumor"
    RESEARCH_GRADE = "research_grade_development"
    MARKET_CONFIRMED_CATALYST = "market_confirmed_breakout_catalyst"
