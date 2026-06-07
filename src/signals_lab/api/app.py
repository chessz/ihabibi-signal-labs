"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from signals_lab.api.routes import health, intelligence, signals
from signals_lab.api.services.intelligence_cache import get_intelligence_cache
from signals_lab.config import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    cache = get_intelligence_cache()
    try:
        await cache.refresh(force=True)
    except Exception:
        logger.warning("startup_intelligence_refresh_failed", exc_info=True)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    api_settings = settings.api

    application = FastAPI(
        title="signals-lab API",
        description="Paper-traded crypto signal research platform",
        version="0.1.0",
        docs_url="/docs" if api_settings.docs_enabled else None,
        redoc_url="/redoc" if api_settings.docs_enabled else None,
        lifespan=lifespan,
    )

    origins = api_settings.cors_origins or [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = api_settings.openapi_prefix.rstrip("/")
    application.include_router(intelligence.router, prefix=prefix)
    application.include_router(signals.router, prefix=prefix)
    application.include_router(health.router, prefix=prefix)

    @application.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
