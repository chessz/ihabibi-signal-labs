"""Health API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProviderHealthSchema(BaseModel):
    provider: str
    status: str
    lag_seconds: int | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None
    tier: str | None = None


class HealthSnapshotSchema(BaseModel):
    overall_status: str
    providers: list[ProviderHealthSchema] = Field(default_factory=list)
    timestamp: datetime
    schema_version: str = "1.0.0"
