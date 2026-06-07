"""News intelligence providers."""

from signals_lab.ingestion.providers.news.cryptocurrency_cv import CryptocurrencyCvProvider
from signals_lab.ingestion.providers.news.rss_feed import RssFanInProvider

__all__ = ["CryptocurrencyCvProvider", "RssFanInProvider"]
