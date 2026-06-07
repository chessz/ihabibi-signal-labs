"""Load config/intelligence.yaml for Tier A feeds and scoring knobs."""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from signals_lab.config import _find_project_root


class RssFeedConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    url: str
    original_source: str
    credibility: float = 0.7
    source_type: str = "news"
    enabled: bool = True


class IntelligenceConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    rss_feeds: list[RssFeedConfig] = Field(default_factory=list)
    asset_keywords: dict[str, list[str]] = Field(default_factory=dict)
    tier_b_enrichers: list[str] = Field(default_factory=list)
    fallbacks: dict[str, dict[str, str]] = Field(default_factory=dict)
    fusion_weights: dict[str, float] = Field(default_factory=dict)
    dedup: dict[str, Any] = Field(default_factory=dict)
    clickbait_patterns: list[str] = Field(default_factory=list)

    def credibility_for_feed(self, feed_id: str) -> Decimal:
        for feed in self.rss_feeds:
            if feed.id == feed_id:
                return Decimal(str(feed.credibility))
        return Decimal("0.5")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def get_intelligence_config(reload: bool = False) -> IntelligenceConfig:
    if reload:
        get_intelligence_config.cache_clear()
    root = _find_project_root()
    data = _load_yaml(root / "config" / "intelligence.yaml")
    return IntelligenceConfig(**data)
