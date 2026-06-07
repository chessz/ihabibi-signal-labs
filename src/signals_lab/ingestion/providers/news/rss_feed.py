"""Direct RSS feed ingestion — Tier A fallback and primary fan-in."""

from __future__ import annotations

import contextlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any

import httpx

from signals_lab.config import ProviderConfig
from signals_lab.domain.intelligence import RawIntelligenceRecord
from signals_lab.domain.intelligence_enums import ContentRole, IntelligenceSourceType, ProviderTier
from signals_lab.ingestion.providers.base_intelligence import BaseIntelligenceProvider
from signals_lab.intelligence.config_loader import RssFeedConfig, get_intelligence_config

_STRIP_TAGS = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return unescape(_STRIP_TAGS.sub(" ", text)).strip()


def _parse_rss_or_atom(xml_text: str, feed: RssFeedConfig) -> list[RawIntelligenceRecord]:
    records: list[RawIntelligenceRecord] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return records

    # RSS 2.0: channel/item
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    source_type = IntelligenceSourceType(feed.source_type)
    cred = Decimal(str(feed.credibility))

    for item in items[:40]:
        title_el = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
        title = _strip_html(title_el.text or "") if title_el is not None and title_el.text else ""
        if not title:
            continue

        link_el = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
        url: str | None = None
        if link_el is not None:
            url = link_el.text or link_el.get("href")

        desc_el = item.find("description") or item.find("{http://www.w3.org/2005/Atom}summary")
        body = _strip_html(desc_el.text or "") if desc_el is not None and desc_el.text else ""

        pub_el = (
            item.find("pubDate")
            or item.find("{http://www.w3.org/2005/Atom}published")
            or item.find("{http://www.w3.org/2005/Atom}updated")
        )
        observed_at = datetime.utcnow()
        if pub_el is not None and pub_el.text:
            try:
                observed_at = parsedate_to_datetime(pub_el.text.strip()).replace(tzinfo=None)
            except (TypeError, ValueError, IndexError):
                with contextlib.suppress(ValueError):
                    observed_at = datetime.fromisoformat(
                        pub_el.text.replace("Z", "+00:00")
                    ).replace(tzinfo=None)

        guid_el = item.find("guid")
        guid = guid_el.text if guid_el is not None and guid_el.text else url or title

        records.append(
            RawIntelligenceRecord(
                external_id=f"rss:{feed.id}:{guid}",
                provider="rss_fan_in",
                provider_tier=ProviderTier.A,
                source_type=source_type,
                original_source=feed.original_source,
                observed_at=observed_at,
                title=title,
                body=body[:2000],
                url=url,
                language="en",
                base_credibility=cred,
                content_role=ContentRole.PRIMARY,
                raw_payload={"feed_id": feed.id},
            )
        )
    return records


class RssFanInProvider(BaseIntelligenceProvider):
    """Fetch all enabled RSS feeds from config/intelligence.yaml."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._feeds = [
            f for f in get_intelligence_config().rss_feeds if f.enabled
        ]

    async def start(self) -> None:
        self._http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "signals-lab/0.1", "Accept": "application/rss+xml, application/xml"},
            follow_redirects=True,
        )

    async def fetch(self) -> list[RawIntelligenceRecord]:
        if self._http_client is None:
            await self.start()
        assert self._http_client is not None

        all_records: list[RawIntelligenceRecord] = []
        for feed in self._feeds:
            try:
                response = await self._http_client.get(feed.url)
                response.raise_for_status()
                all_records.extend(_parse_rss_or_atom(response.text, feed))
            except httpx.HTTPError as exc:
                self._logger.warning("rss_feed_fetch_failed", feed=feed.id, error=str(exc))
        return all_records

    async def validate_response(self, response: Any) -> bool:
        return isinstance(response, list)
