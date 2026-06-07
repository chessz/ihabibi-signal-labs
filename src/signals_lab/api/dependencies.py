"""FastAPI dependency injection."""

from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException, status

from signals_lab.api.services.intelligence_cache import IntelligenceCache, get_intelligence_cache
from signals_lab.api.services.signal_catalog import SignalCatalog, get_signal_catalog
from signals_lab.config import Settings, get_settings


def get_app_settings() -> Settings:
    return get_settings()


def get_intel_cache() -> IntelligenceCache:
    return get_intelligence_cache()


def get_signals() -> SignalCatalog:
    return get_signal_catalog()


async def optional_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> str | None:
    """Optional API key — Stage 3 will enforce; dev mode allows anonymous read."""
    return x_api_key


async def require_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> str:
    settings = get_settings()
    expected = settings.api.api_key if hasattr(settings, "api") else None
    if expected and x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key",
        )
    return x_api_key or "anonymous"
