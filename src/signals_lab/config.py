"""Configuration system for signals-lab.

Loads YAML config and environment variables into typed Pydantic models.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import os

import yaml
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic_settings import BaseSettings


# ---------------------------------------------------------------------------
# Helper: find project root
# ---------------------------------------------------------------------------

def _find_project_root() -> Path:
    """Walk upward from CWD to find pyproject.toml."""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Could not find pyproject.toml in any parent directory")


def _load_yaml_overrides(yaml_path: Path) -> Dict[str, Any]:
    """Load YAML config file, return empty dict if missing."""
    if not yaml_path.exists():
        return {}
    with open(yaml_path, "r") as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# Config model classes
# ---------------------------------------------------------------------------

class AppSettings(BaseModel):
    """Core application settings."""
    model_config = ConfigDict(frozen=True)

    name: str = "signals-lab"
    environment: str = "development"
    log_level: str = "INFO"
    timezone: str = "UTC"


class DatabaseSettings(BaseModel):
    """Database connection settings."""
    model_config = ConfigDict(frozen=True)

    url: str = "postgresql://postgres:postgres@localhost:5432/signals_ts"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


class StorageSettings(BaseModel):
    """Storage configuration."""
    model_config = ConfigDict(frozen=True)

    timeseries: DatabaseSettings = Field(default_factory=DatabaseSettings)
    relational: DatabaseSettings = Field(default_factory=DatabaseSettings)


class ProviderConfig(BaseModel):
    """Data provider configuration."""
    model_config = ConfigDict(frozen=True, extra="allow")

    name: str
    type: str = "rest"
    enabled: bool = True
    tier: str = "A"
    base_url: Optional[str] = None
    symbols: List[str] = Field(default_factory=list)
    assets: List[str] = Field(default_factory=list)
    api_key_env: Optional[str] = None
    rate_limit_per_minute: int = 60
    websocket_enabled: bool = False
    query: Optional[str] = None
    language: Optional[str] = None
    page_size: Optional[int] = None
    filter: Optional[str] = None
    public: Optional[str] = None
    metrics: List[str] = Field(default_factory=list)


class IngestionServiceSettings(BaseModel):
    """Settings for a single ingestion service."""
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    interval_seconds: int = 60
    batch_size: int = 100
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_backoff_seconds: int = 5
    providers: List[ProviderConfig] = Field(default_factory=list)


class IngestionSettings(BaseModel):
    """All ingestion services configuration."""
    model_config = ConfigDict(frozen=True)

    market: IngestionServiceSettings = Field(default_factory=IngestionServiceSettings)
    social: IngestionServiceSettings = Field(default_factory=IngestionServiceSettings)
    onchain: IngestionServiceSettings = Field(default_factory=IngestionServiceSettings)
    events: IngestionServiceSettings = Field(default_factory=IngestionServiceSettings)
    intelligence: IngestionServiceSettings = Field(default_factory=IngestionServiceSettings)


class FeatureFamilyParams(BaseModel):
    """Parameters for a single feature family."""
    model_config = ConfigDict(frozen=True, extra="allow")

    enabled: bool = True
    params: Dict[str, Any] = Field(default_factory=dict)


class FeatureFamilySettings(BaseModel):
    """Feature family groupings."""
    model_config = ConfigDict(frozen=True)

    trend: FeatureFamilyParams = Field(default_factory=FeatureFamilyParams)
    momentum: FeatureFamilyParams = Field(default_factory=FeatureFamilyParams)
    mean_reversion: FeatureFamilyParams = Field(default_factory=FeatureFamilyParams)
    volatility: FeatureFamilyParams = Field(default_factory=FeatureFamilyParams)
    social: FeatureFamilyParams = Field(default_factory=FeatureFamilyParams)
    onchain: FeatureFamilyParams = Field(default_factory=FeatureFamilyParams)
    events: FeatureFamilyParams = Field(default_factory=FeatureFamilyParams)
    cross_asset: FeatureFamilyParams = Field(default_factory=FeatureFamilyParams)


class FeatureSettings(BaseModel):
    """Feature engine settings."""
    model_config = ConfigDict(frozen=True)

    computation_windows: List[str] = Field(default_factory=lambda: ["1h", "4h", "1d"])
    lookback_periods: int = 500
    min_data_points: int = 50
    families: FeatureFamilySettings = Field(default_factory=FeatureFamilySettings)


class ConfidenceBandRange(BaseModel):
    """Range for a confidence band."""
    model_config = ConfigDict(frozen=True)

    low: float = 0
    high: float = 100


class SignalSettings(BaseModel):
    """Signal generation settings."""
    model_config = ConfigDict(frozen=True)

    min_confidence_for_publish: float = 70
    confidence_bands: Dict[str, List[float]] = Field(
        default_factory=lambda: {
            "low": [0, 40],
            "medium": [40, 60],
            "high": [60, 80],
            "extreme": [80, 100],
        }
    )
    rule_version: str = "v1.0.0"
    max_signals_per_asset: int = 1
    signal_cooldown_hours: int = 4
    expiry_hours_by_horizon: Dict[str, int] = Field(
        default_factory=lambda: {"1h": 4, "4h": 12, "1d": 48, "1w": 168}
    )
    default_horizon: str = "4h"
    regime_filters: Dict[str, Any] = Field(default_factory=dict)
    risk_management: Dict[str, Any] = Field(default_factory=dict)


class PaperTradingSettings(BaseModel):
    """Paper trading simulation settings."""
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    fee_bps: int = 10
    slippage_bps: int = 5
    initial_capital_usd: float = 100000
    max_position_pct: float = 0.10
    max_open_positions: int = 10
    allow_short: bool = True
    compound_returns: bool = True


class MetricsSettings(BaseModel):
    """Evaluation metrics settings."""
    model_config = ConfigDict(frozen=True)

    window_days: int = 30
    min_trades_for_stats: int = 10
    confidence_band_analysis: bool = True
    regime_analysis: bool = True
    signal_class_analysis: bool = True
    decay_analysis: bool = True
    sell_timing_analysis: bool = True


class ReportingSettings(BaseModel):
    """Report generation settings."""
    model_config = ConfigDict(frozen=True)

    generate_daily: bool = True
    generate_weekly: bool = True
    generate_monthly: bool = True
    output_format: str = "json"
    output_path: str = "./reports"


class EvaluationSettings(BaseModel):
    """Evaluation module settings."""
    model_config = ConfigDict(frozen=True)

    paper_trading: PaperTradingSettings = Field(default_factory=PaperTradingSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    reporting: ReportingSettings = Field(default_factory=ReportingSettings)


class ApiKeyConfig(BaseModel):
    """API key configuration for downstream consumers."""
    model_config = ConfigDict(frozen=True)

    name: str
    key_env: str
    permissions: List[str] = Field(default_factory=list)


class ApiSettings(BaseModel):
    """API server settings."""
    model_config = ConfigDict(frozen=True)

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = True
    rate_limit: str = "100/minute"
    cors_origins: List[str] = Field(default_factory=list)
    api_keys: List[ApiKeyConfig] = Field(default_factory=list)
    docs_enabled: bool = True
    openapi_prefix: str = "/api/v1"


class WorkerConfig(BaseModel):
    """Single background worker configuration."""
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    concurrency: int = 1
    schedule_cron: Optional[str] = None
    graceful_shutdown_timeout: int = 30


class WorkerSettings(BaseModel):
    """Background worker settings."""
    model_config = ConfigDict(frozen=True)

    ingestion: WorkerConfig = Field(default_factory=WorkerConfig)
    features: WorkerConfig = Field(default_factory=WorkerConfig)
    signals: WorkerConfig = Field(default_factory=WorkerConfig)
    evaluation: WorkerConfig = Field(default_factory=WorkerConfig)


class LoggingSettings(BaseModel):
    """Logging configuration."""
    model_config = ConfigDict(frozen=True)

    level: str = "INFO"
    format: str = "json"
    output: str = "stdout"
    structured: bool = True
    include_timestamp: bool = True
    include_level: bool = True
    include_logger: bool = True
    sampling_rate: float = 1.0


# ---------------------------------------------------------------------------
# Top-level Settings
# ---------------------------------------------------------------------------

class Settings(BaseModel):
    """Top-level settings aggregator."""
    model_config = ConfigDict(frozen=True)

    app: AppSettings = Field(default_factory=AppSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    ingestion: IngestionSettings = Field(default_factory=IngestionSettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)
    signals: SignalSettings = Field(default_factory=SignalSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    workers: WorkerSettings = Field(default_factory=WorkerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @classmethod
    def load(
        cls,
        yaml_path: Optional[Path] = None,
        env_prefix: str = "SIGNALSLAB_",
    ) -> Settings:
        """Load settings from YAML file with environment variable overrides.

        Args:
            yaml_path: Path to YAML config file. Defaults to config/settings.yaml
                       relative to project root.
            env_prefix: Prefix for environment variable overrides.
        """
        project_root = _find_project_root()

        if yaml_path is None:
            yaml_path = project_root / "config" / "settings.yaml"

        yaml_data = _load_yaml_overrides(yaml_path)

        # Merge environment variable overrides (dot-notation keys)
        env_overrides: Dict[str, Any] = {}
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                _set_nested(env_overrides, config_key.split("__"), value)

        merged = _deep_merge(yaml_data, env_overrides)
        return cls(**merged)


# ---------------------------------------------------------------------------
# Singleton cache
# ---------------------------------------------------------------------------

_settings_cache: Optional[Settings] = None


def get_settings(reload: bool = False) -> Settings:
    """Get cached settings instance, loading if necessary."""
    global _settings_cache
    if _settings_cache is None or reload:
        _settings_cache = Settings.load()
    return _settings_cache


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _set_nested(d: Dict[str, Any], keys: List[str], value: str) -> None:
    """Set a value in a nested dict using dot-separated keys.

    Environment var SIGNALSLAB_STORAGE__TIMESERIES__POOL_SIZE=20 becomes
    {"storage": {"timeseries": {"pool_size": "20"}}}
    """
    for key in keys[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]  # type: ignore[assignment]
    # Cast numeric-looking values
    final_key = keys[-1]
    try:
        d[final_key] = int(value)
        return
    except (ValueError, TypeError):
        pass
    try:
        d[final_key] = float(value)
        return
    except (ValueError, TypeError):
        pass
    if value.lower() in ("true", "false"):
        d[final_key] = value.lower() == "true"
        return
    d[final_key] = value


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, override taking precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result