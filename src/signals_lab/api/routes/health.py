"""Health snapshot routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from signals_lab.api.schemas.health import HealthSnapshotSchema, ProviderHealthSchema
from signals_lab.config import get_settings
from signals_lab.utils.health import HealthChecker, HealthStatus

router = APIRouter(prefix="/health", tags=["health"])

_STATUS_MAP = {
    HealthStatus.OK: "UP",
    HealthStatus.WARN: "DEGRADED",
    HealthStatus.FAIL: "DOWN",
    HealthStatus.SKIP: "UNKNOWN",
}


def _overall(providers: list[ProviderHealthSchema]) -> str:
    if any(p.status == "DOWN" for p in providers):
        return "degraded"
    if any(p.status == "DEGRADED" for p in providers):
        return "degraded"
    return "healthy"


@router.get("", response_model=HealthSnapshotSchema)
async def get_health() -> HealthSnapshotSchema:
    settings = get_settings()
    checker = HealthChecker(settings=settings)
    results = await checker.run_apis()

    tier_by_name: dict[str, str] = {}
    for svc_name in ("intelligence", "market", "events", "social"):
        svc = getattr(settings.ingestion, svc_name, None)
        if svc is None:
            continue
        for provider in svc.providers:
            tier = getattr(provider, "tier", None)
            if tier:
                tier_by_name[provider.name] = str(tier)

    providers: list[ProviderHealthSchema] = []
    for result in results:
        if result.category != "api":
            continue
        status = _STATUS_MAP.get(result.status, "UNKNOWN")
        providers.append(
            ProviderHealthSchema(
                provider=result.name,
                status=status,
                lag_seconds=result.latency_ms // 1000 if result.latency_ms else None,
                last_success_at=datetime.utcnow() if status == "UP" else None,
                last_error=None if status == "UP" else result.message,
                tier=tier_by_name.get(result.name),
            )
        )

    return HealthSnapshotSchema(
        overall_status=_overall(providers),
        providers=providers,
        timestamp=datetime.utcnow(),
    )
