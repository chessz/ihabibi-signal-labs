"""cryptocurrency.cv Tier A news aggregator provider."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
from typing import Any
from uuid import uuid4

import httpx

from signals_lab.config import ProviderConfig
from signals_lab.domain.enums import ProviderStatus
from signals_lab.domain.intelligence import RawIntelligenceRecord
from signals_lab.domain.intelligence_enums import ContentRole, IntelligenceSourceType, ProviderTier
from signals_lab.ingestion.providers.base_intelligence import BaseIntelligenceProvider

_DEFAULT_BASE = "https://cryptocurrency.cv"
_DEFAULT_LIMIT = 30


class CryptocurrencyCvProvider(BaseIntelligenceProvider):
    """Fetch crypto news from cryptocurrency.cv JSON API (Tier A)."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._base_url = (config.base_url or _DEFAULT_BASE).rstrip("/")
        self._limit = getattr(config, "page_size", None) or _DEFAULT_LIMIT

    async def start(self) -> None:
        self._http_client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "signals-lab/0.1"},
        )
        self._status = ProviderStatus.HEALTHY

    async def fetch(self) -> list[RawIntelligenceRecord]:
        if self._http_client is None:
            await self.start()
        assert self._http_client is not None

        response = await self._http_client.get(
            "/api/news",
            params={"limit": self._limit},
        )
        response.raise_for_status()
        payload = response.json()
        articles = payload.get("articles") or payload.get("data") or []
        if not isinstance(articles, list):
            return []

        records: list[RawIntelligenceRecord] = []
        for article in articles:
            parsed = self._parse_article(article)
            if parsed is not None:
                records.append(parsed)
        return records

    def _parse_article(self, article: dict[str, Any]) -> RawIntelligenceRecord | None:
        title = (article.get("title") or "").strip()
        if not title:
            return None

        url = article.get("url") or article.get("link")
        source_name = article.get("source") or article.get("sourceName") or "cryptocurrency.cv"
        if isinstance(source_name, dict):
            source_name = source_name.get("name") or "unknown"

        external_id = str(article.get("id") or article.get("guid") or url or uuid4())
        observed_at = self._parse_time(
            article.get("publishedAt")
            or article.get("published_at")
            or article.get("pubDate")
        )
        body = (article.get("description") or article.get("summary") or article.get("content") or "")[:2000]

        return RawIntelligenceRecord(
            external_id=f"cv:{external_id}",
            provider=self.name,
            provider_tier=ProviderTier.A,
            source_type=IntelligenceSourceType.NEWS,
            original_source=str(source_name),
            observed_at=observed_at,
            title=title,
            body=body,
            url=url,
            language=str(article.get("language") or "en")[:2],
            base_credibility=Decimal("0.72"),
            content_role=ContentRole.PRIMARY,
            raw_payload={"source_api": "cryptocurrency.cv"},
        )

    @staticmethod
    def _parse_time(value: Any) -> datetime:
        if value is None:
            return datetime.utcnow()
        if isinstance(value, datetime):
            return value
        text = str(value)
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            pass
        try:
            return parsedate_to_datetime(text).replace(tzinfo=None)
        except (TypeError, ValueError, IndexError):
            return datetime.utcnow()

    async def validate_response(self, response: Any) -> bool:
        return isinstance(response, list)
