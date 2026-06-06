# signals-lab — Technical Specifications

> **Status:** Alpha (v0.1.0) — Stage 1 / Stage 2 in progress
> **Last updated:** 2026-06-06
> **Audience:** Engineers, researchers, and AI coding agents working on the platform
> **Companion docs:** `README.md` (overview), `ARCHITECTURE.md` (high-level design)

---

## 1. Mission & Scope

**signals-lab** is a high-performance, research-grade crypto market signal platform that:

1. **Ingests** market (OHLCV, funding, OI), social/sentiment, on-chain, and event/geopolitical data
2. **Computes** reusable, versioned research features across multiple time windows
3. **Generates** ranked BUY / SELL / WATCH signals with explainable confidence scores
4. **Tracks** paper-trading outcomes and full P/L analytics
5. **Publishes** approved (high / extreme confidence) signals and performance metrics via a FastAPI for the downstream [iHabibi Trading](https://ihabibi.com) consumer

**Non-goals (explicit):**
- ❌ **No live trading.** No exchange orders are placed — ever.
- ❌ No auto-execution, no broker connectivity, no custody of funds.
- ❌ No retail-facing UI (the platform is consumed via the API).
- ✅ Strict out-of-sample evaluation, walk-forward validation, look-ahead bias prevention.

---

## 2. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | **Python 3.11+** | Pydantic v2, `asyncio`, `aiohttp` |
| API framework | **FastAPI** + Uvicorn | Auto OpenAPI, async, type-driven |
| Time-series DB | **TimescaleDB** (PostgreSQL extension) | Hypertables, native SQL |
| Relational DB | **PostgreSQL** | `asyncpg`, `SQLAlchemy 2.0`, `alembic` migrations |
| Validation / config | **Pydantic v2** + `pydantic-settings` | Strict, env-aware, YAML overlay |
| Data processing | **NumPy**, **pandas**, **TA-Lib** | Technical analysis |
| Scheduling | **APScheduler** | Cron + interval jobs |
| HTTP / WS | **aiohttp**, **httpx**, **websockets** | Async-first |
| Serialization | **orjson**, **msgpack** | Fast |
| Logging | **structlog** (JSON, structured) | Contextual, grep-friendly |
| CLI | **Typer** + Rich | Single `signals_lab` entrypoint |
| Metrics | **prometheus-client** | `/metrics` endpoint |
| Testing | **pytest** + pytest-asyncio | Unit + integration + fixtures |
| Lint / type | **ruff** + **mypy --strict** | CI-blocking |
| Optional event bus | **NATS** (`nats-py`) | Disabled by default; enabled per `events.enabled: true` |

---

## 3. Repository Layout

```
signals-lab/
├── config/
│   └── settings.yaml              # Single source of truth for runtime config
├── docs/                          # (planned) architecture.md, api.md, data-model.md
├── scripts/                       # (planned) migrate.py, seed.py, dev-setup.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── src/signals_lab/
│   ├── __init__.py                # Package marker
│   ├── config.py                  # Pydantic settings, YAML + env overlay, get_settings()
│   ├── cli/                       # (planned) Typer CLI entrypoint
│   ├── domain/                    # Pure Pydantic models, NO I/O
│   │   ├── enums.py               # All enums (SignalClass, ConfidenceBand, ...)
│   │   ├── market.py              # AssetPair, MarketObservation
│   │   ├── social.py              # SocialObservation
│   │   ├── onchain.py             # OnChainObservation
│   │   ├── events.py              # EventObservation
│   │   ├── features.py            # FeatureDefinition, FeatureVector, FeatureBatch
│   │   ├── signals.py             # Signal, ContributingFactor, Stop/SellLogic, ProvenanceRecord
│   │   └── evaluation.py          # PaperPosition, EvaluationMetrics, DecayAnalysis, SellTimingMetrics
│   ├── storage/                   # Repository pattern, I/O boundary
│   │   ├── repository.py          # Abstract interfaces: TimeSeriesRepository, RelationalRepository
│   │   ├── timeseries.py          # TimescaleDBClient (asyncpg + hypertables)
│   │   └── relational.py          # PostgresRelationalClient (signals, positions, metrics, config)
│   ├── ingestion/                 # Data acquisition workers
│   │   ├── base.py                # BaseProvider, BaseIngestor
│   │   ├── market_ingestor.py     # Binance REST + WS
│   │   ├── social_ingestor.py     # LunarCrush
│   │   ├── onchain_ingestor.py    # Glassnode (disabled by default)
│   │   ├── event_ingestor.py      # NewsAPI + CryptoPanic
│   │   └── scheduler.py           # IngestionScheduler — orchestrates all fetch loops
│   ├── features/                  # (planned) FeatureEngine, families/{trend,momentum,...}
│   ├── signals/                   # (planned) SignalEngine, RuleEngine, ConfidenceCalibrator
│   ├── evaluation/                # (planned) PaperTrader, MetricsCalculator, DecayTracker
│   ├── api/                       # (planned) FastAPI app + routes + schemas + auth
│   ├── workers/                   # (planned) Background workers (ingestion/feature/signal/eval)
│   ├── events/                    # (planned) Optional NATS event bus
│   └── utils/
│       ├── datetime.py            # UTC helpers, window parsing
│       └── logging.py             # structlog configuration
├── .env.example                   # Template for required env vars
├── .gitignore
├── ARCHITECTURE.md                # High-level architecture
├── README.md                      # Quick-start + overview
├── SPECS.md                       # This file
├── AGENTS.md                      # AI agent guidance
└── pyproject.toml                 # Dependencies + tooling config
```

---

## 4. Data Contracts (Domain)

### 4.1 Core enums (`src/signals_lab/domain/enums.py`)

| Enum | Members | Notes |
|---|---|---|
| `SignalClass` | `LONG_CANDIDATE`, `SHORT_CANDIDATE`, `WATCH_ONLY`, `IGNORE` | Output class of a signal |
| `ConfidenceBand` | `LOW` (0–40), `MEDIUM` (40–60), `HIGH` (60–80), `EXTREME` (80–100) | Calibrated from `confidence_score` |
| `SignalSide` | `BUY`, `SELL`, `NEUTRAL` | Trade direction |
| `MarketRegime` | `TRENDING_UP`, `TRENDING_DOWN`, `RANGING`, `VOLATILE`, `UNKNOWN` | Regime gate |
| `DataSourceType` | `MARKET`, `ONCHAIN`, `SOCIAL`, `EVENTS` | Source category |
| `SignalStatus` | `ACTIVE`, `EXPIRED`, `INVALIDATED`, `FILLED_PAPER`, `CANCELLED` | Signal lifecycle |
| `PositionStatus` | `OPEN`, `CLOSED`, `STOPPED`, `EXPIRED`, `LIQUIDATED` | Paper position lifecycle |
| `ObservationType` | `MARKET`, `SOCIAL`, `ONCHAIN`, `EVENTS`, `FEATURES` | Storage routing key |
| `ProviderStatus` | `HEALTHY`, `DEGRADED`, `DOWN`, `RATE_LIMITED`, `UNKNOWN` | Provider health |
| `WorkerStatus` | `STARTING`, `RUNNING`, `PAUSED`, `STOPPING`, `STOPPED`, `ERROR` | Worker lifecycle |
| `EventSeverity` | `1..5` (int enum) | LOW..CRITICAL |
| `EventType` | `REGULATORY`, `ETF`, `EXCHANGE_INCIDENT`, `GEOPOLITICAL`, `MACRO`, `TECHNICAL`, `CORPORATE`, `UNKNOWN` | Event taxonomy |
| `FeatureFamily` | `TREND`, `MOMENTUM`, `MEAN_REVERSION`, `VOLATILITY`, `SOCIAL`, `ONCHAIN`, `EVENTS`, `CROSS_ASSET` | Feature grouping |
| `InvalidationReason` | `STOP_LOSS_HIT`, `TAKE_PROFIT_HIT`, `TIME_EXPIRY`, `REGIME_CHANGE`, `CONFIDENCE_DROPPED`, `NEW_CONTRADICTING_SIGNAL`, `MANUAL_CANCEL` | Why a signal was killed |
| `ExitReason` | `STOP_LOSS`, `TAKE_PROFIT`, `TIME_BASED`, `SIGNAL_REVERSAL`, `REGIME_CHANGE`, `MANUAL`, `EXPIRED` | Why a position was closed |

### 4.2 Signal core contract

```python
class Signal(BaseModel):
    signal_id: UUID                              # Unique
    asset_pair: AssetPair
    signal_class: SignalClass                    # long/short/watch/ignore
    side: SignalSide                             # buy/sell/neutral
    confidence_score: Decimal                     # 0..100
    confidence_band: ConfidenceBand               # Derived from score via settings.signals.confidence_bands
    generated_at: datetime                       # UTC
    expiry_at: Optional[datetime]                # horizon-based
    regime: MarketRegime
    thesis: str                                   # >= 10 chars, human-readable
    contributing_factors: List[ContributingFactor]
    invalidation_condition: str                   # >= 5 chars
    suggested_stop: Optional[StopLogic]
    suggested_sell: Optional[SellLogic]
    expected_holding_horizon: str                 # "1h" | "4h" | "1d" | "1w"
    provenance: ProvenanceRecord
    status: SignalStatus
    entry_price: Optional[Decimal]
    target_price: Optional[Decimal]
    metadata: Dict[str, Any]

    @property
    def is_publishable(self) -> bool:             # HIGH or EXTREME only
    @property
    def is_active(self) -> bool:
    @property
    def is_expired(self) -> bool:
    @property
    def primary_direction(self) -> str:           # bullish/bearish/neutral
```

**Invariants enforced by Pydantic:**
- `confidence_score ∈ [0, 100]`
- `ContributingFactor.weight ∈ [0, 1]`
- `thesis.length >= 10`, `invalidation_condition.length >= 5`
- `confidence_band` is consistent with `confidence_score` (validated in service layer)
- `is_publishable == (confidence_band in {HIGH, EXTREME})`

### 4.3 Paper position contract

```python
class PaperPosition(BaseModel):
    position_id: UUID
    signal_id: UUID
    asset_pair: AssetPair
    side: SignalSide
    entry_price: Decimal
    entry_time: datetime
    quantity: Decimal                             # > 0
    notional_usd: Decimal                         # >= 0
    stop_price: Optional[Decimal]
    target_price: Optional[Decimal]
    status: PositionStatus
    exit_price: Optional[Decimal]
    exit_time: Optional[datetime]
    exit_reason: Optional[ExitReason]
    pnl_usd: Optional[Decimal]
    pnl_pct: Optional[Decimal]
    fees_usd: Decimal
    slippage_usd: Decimal
    max_favorable_excursion_pct: Optional[Decimal]
    max_adverse_excursion_pct: Optional[Decimal]
    holding_period_hours: Optional[Decimal]
    is_win: Optional[bool]
    signal_confidence_band: Optional[ConfidenceBand]
    signal_regime: Optional[MarketRegime]
    signal_class: Optional[SignalClass]
    tags: Dict[str, Any]
```

---

## 5. Storage Specification

### 5.1 Time-series (TimescaleDB)

| Hypertable | Tag columns | Payload (JSONB) | Source |
|---|---|---|---|
| `market_observations` | `symbol`, `exchange`, `source` | OHLCV, volume, `spread_bps`, `realized_volatility`, `funding_rate`, `open_interest` | `MarketIngestor` |
| `social_observations` | `symbol`, `exchange` (=`"social"`), `source` | `mention_count`, `sentiment_score` (-1..1), `sentiment_positive/negative/neutral`, `influencer_mentions`, `social_dominance_pct`, `topic_tags` | `SocialIngestor` |
| `onchain_observations` | `symbol`, `exchange`, `source` | exchange inflow/outflow USD, whale tx count/volume, stablecoin mint/redeem, supply on exchanges %, large holder net flow | `OnChainIngestor` |
| `event_observations` | `symbol`, `exchange` (=`"events"`), `source` | `event_type`, `title`, `description`, `severity` (1..5), `affected_assets`, `region`, `country_sentiment`, `market_impact_estimate`, `tags`, `url` | `EventIngestor` |
| `feature_vectors` | `symbol`, `exchange`, `source` | `feature_family`, `feature_name`, `value`, `window`, `computation_version` | Feature engine |

**Schema DDL pattern (TimescaleDB):**
```sql
CREATE TABLE IF NOT EXISTS {table} (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    exchange    TEXT        NOT NULL,
    source      TEXT        NOT NULL,
    payload     JSONB       NOT NULL,
    UNIQUE (time, symbol, exchange, source)
);
SELECT create_hypertable('{table}', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_{table}_symbol ON {table} (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_{table}_time   ON {table} (time DESC);
```

**Conflict resolution:** `(time, symbol, exchange, source)` is unique — re-ingestion is idempotent. `ON CONFLICT ... DO NOTHING` is the default.

**Hypertables are created lazily on `TimescaleDBClient.create()`** — if the TimescaleDB extension is missing, the code logs a warning and continues with regular tables.

### 5.2 Relational (PostgreSQL)

| Table | Purpose | Key fields |
|---|---|---|
| `asset_pairs` | Trading pair catalog | `symbol`, `base`, `quote`, `exchange`, `is_active`, `metadata` |
| `providers` | Provider registry | `name`, `type`, `base_url`, `rate_limit`, `last_status`, encrypted `api_key` |
| `signals` | All generated signals (including un-published) | full `Signal` payload, `signal_id` PK, indexed by `generated_at`, `asset_pair`, `confidence_band` |
| `paper_positions` | Lifecycle of paper trades | full `PaperPosition`, `position_id` PK, indexed by `entry_time`, `status`, `signal_id` |
| `evaluation_metrics` | Pre-computed aggregates | `period_start/end`, `metric_name`, `metric_value`, `breakdown_dim`, `breakdown_value` |
| `signal_rules` | Versioned ruleset | `rule_id`, `version`, `signal_class`, `conditions` JSONB, `enabled` |
| `feature_registry` | Feature definitions | `name`, `family`, `computation_function`, `params`, `enabled`, `version` |
| `worker_runs` | Audit log | `worker`, `started_at`, `ended_at`, `status`, `error` |
| `api_keys` | Downstream consumer auth | `name` (FK), `key_hash`, `permissions[]`, `last_used_at` |

**Repository interfaces (`storage/repository.py`):**
- `TimeSeriesRepository.store_observation / store_batch / query / get_latest`
- `RelationalRepository.{crud per entity}`

---

## 6. Configuration Specification

Loaded by `src/signals_lab/config.py` via `get_settings()`. The precedence is:

1. Environment variables matching `SIGNALSLAB_*` (double underscore = nested), e.g. `SIGNALSLAB_STORAGE__TIMESERIES__POOL_SIZE=20`
2. `config/settings.yaml`
3. Pydantic defaults (in `config.py`)

**Top-level config tree:**

```
app          → AppSettings         # name, environment, log_level, timezone
storage      → StorageSettings     # timeseries, relational (each DatabaseSettings)
ingestion    → IngestionSettings   # market/social/onchain/events → IngestionServiceSettings
features     → FeatureSettings     # computation_windows, lookback_periods, families
signals      → SignalSettings      # min_confidence_for_publish, confidence_bands, ...
evaluation   → EvaluationSettings  # paper_trading, metrics, reporting
api          → ApiSettings         # host, port, workers, rate_limit, api_keys[], ...
workers      → WorkerSettings      # ingestion/features/signals/evaluation
logging      → LoggingSettings     # level, format, structured
```

**Defaults that matter:**
- `signals.min_confidence_for_publish = 70` (HIGH band)
- `signals.signal_cooldown_hours = 4`
- `signals.max_signals_per_asset = 1`
- `signals.expiry_hours_by_horizon = {1h: 4, 4h: 12, 1d: 48, 1w: 168}`
- `evaluation.paper_trading.fee_bps = 10`, `slippage_bps = 5`, `initial_capital_usd = 100000`
- `evaluation.paper_trading.max_position_pct = 0.10`, `max_open_positions = 10`
- `evaluation.metrics.window_days = 30`, `min_trades_for_stats = 10`
- `api.rate_limit = "100/minute"`, `api.cors_origins = ["localhost:3000", "localhost:8080"]`

---

## 7. Ingestion Specification

### 7.1 Ingestor contract

All ingestors extend `BaseIngestor` and implement:

```python
class BaseIngestor:
    name: str                                  # "market", "social", "onchain", "events"
    observation_type: ObservationType
    providers: List[BaseProvider]

    async def start() -> None
    async def stop() -> None
    async def fetch_all() -> List[Observation]  # One call returns N observations
    async def health_check() -> Dict[str, ProviderStatus]
```

Each provider is a `BaseProvider` subclass implementing:

```python
class BaseProvider:
    name: str
    async def fetch() -> List[Dict[str, Any]]   # Raw provider payload
    def normalize(raw: List[Dict]) -> List[Observation]  # → domain objects
    async def health_check() -> ProviderStatus
```

### 7.2 Concrete providers

| Ingestor | Provider | Endpoint(s) | Interval | Symbols / scope | Notes |
|---|---|---|---|---|---|
| `MarketIngestor` | `binance` | REST `/api/v3/klines` + WS `@kline_*` | 60s | BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, XRP/USDT, ADA/USDT, DOGE/USDT, AVAX/USDT | REST fallback if WS fails |
| `SocialIngestor` | `lunarcrush` | `/v2/coins` | 300s | BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX | Requires `LUNARCRUSH_API_KEY` |
| `OnChainIngestor` | `glassnode` | `/v1/metrics` | 900s (15m) | `addresses/active_count`, `transactions/count`, `market/price_usd_close` | **Disabled by default**; enable when API key is configured |
| `EventIngestor` | `newsapi` + `cryptopanic` | `/v2/everything` + `/v1/posts` | 300s | "crypto OR bitcoin OR ethereum OR blockchain" | Deduplicate by URL/title hash |

### 7.3 Scheduler

`IngestionScheduler` (in `ingestion/scheduler.py`):
- One `asyncio.Task` per ingestor running a `_fetch_loop` with the configured `interval_seconds`.
- A `_health_check_loop` runs every 60s, logging warnings for any provider not in `HEALTHY` state.
- `run_once()` executes a single fetch cycle for all ingestors (useful for backfill, tests, ad-hoc runs).
- Graceful shutdown via `stop()` cancels all tasks, awaits them with `return_exceptions=True`, and stops each ingestor.

### 7.4 Reliability patterns

- **Retries:** `tenacity` exponential backoff, `retry_attempts=3`, `retry_backoff_seconds=5–30` per service.
- **Rate limiting:** Per-provider `rate_limit_per_minute` enforced via a token-bucket guard before each request.
- **Idempotency:** Unique constraint `(time, symbol, exchange, source)` + `ON CONFLICT DO NOTHING`.
- **Failure isolation:** A failing ingestor does not block other ingestors (one task per ingestor, exceptions logged, not raised).
- **Mock providers:** `Mock*Provider` classes (planned) inject deterministic fixtures for unit/integration tests.

---

## 8. Feature Engine Specification (Planned)

### 8.1 Feature families and planned features

| Family | Feature examples | Default windows | Computation |
|---|---|---|---|
| `TREND` | SMA(20/50/200), EMA(12/26/50), ADX(14), Parabolic SAR | 1h, 4h, 1d | `ta-lib` |
| `MOMENTUM` | RSI(14), MACD(12/26/9), ROC(10), Stochastic(14/3/3) | 1h, 4h, 1d | `ta-lib` |
| `MEAN_REVERSION` | Bollinger Bands(20, 2σ), Z-score(20), RSI extremes | 1h, 4h, 1d | `pandas` |
| `VOLATILITY` | ATR(14), realized vol(20, annualized 365), vol-regime classification | 1h, 4h, 1d | `numpy` |
| `SOCIAL` | mention velocity, sentiment divergence, dominance shift, influencer concentration | 24h, 48h | `numpy` |
| `ONCHAIN` | flow imbalance, whale net flow, supply concentration, stablecoin flows | 24h | `numpy` |
| `EVENTS` | event risk penalty, catalyst proximity | 72h proximity, 48h decay | rule-based |
| `CROSS_ASSET` | correlation to BTC, beta, sector rotation | 30d correlation, 7d rotation | `numpy` |

### 8.2 Computation rules (CRITICAL)

- **No look-ahead bias.** Features computed at timestamp `t` MUST only use observations with `time ≤ t`.
- **Min data points:** `min_data_points = 50` per window (configurable).
- **Lookback:** `lookback_periods = 500` (most-recent N observations) per asset/window.
- **Versioning:** Every `FeatureVector` carries `computation_version` for reproducibility.
- **Registry:** Definitions persisted in `feature_registry` (PostgreSQL); updateable at runtime.
- **Family gating:** A family with `enabled: false` is skipped end-to-end.

---

## 9. Signal Engine Specification (Planned)

### 9.1 Pipeline

```
FeatureVectors  →  RuleEngine  →  SignalCandidates  →  RankingEngine  →  ConfidenceCalibrator  →  Signals
```

1. **`RuleEngine`:** Loads enabled `SignalRule`s from `signal_rules` table. Each rule specifies:
   - `signal_class` (LONG_CANDIDATE | SHORT_CANDIDATE | WATCH_ONLY)
   - `conditions`: a structured predicate tree over feature names + thresholds
   - `required_features`: subset of features the rule consumes
   - `min_confidence`, `weight`, `cooldown_hours`
2. **`RankingEngine`:** Combines matching candidates into a single per-asset ranking. Respects:
   - `max_signals_per_asset = 1`
   - `signal_cooldown_hours = 4` (no duplicate signal within window)
   - `regime_filters`: `trending_up`/`ranging` allowed for LONG; `trending_down`/`ranging` for SHORT; `volatile`/`unknown` blocked.
3. **`ConfidenceCalibrator`:** Maps `raw_score ∈ [0, 100]` → `confidence_score` and `confidence_band` using `settings.signals.confidence_bands`.
4. **Thesis & invalidation:** Template-based, with the top 3 `ContributingFactor`s rendered into the `thesis`. `invalidation_condition` is rule-defined.

### 9.2 Publishing rule

- `is_publishable == (confidence_band ∈ {HIGH, EXTREME})`
- API exposes only publishable signals; lower bands stay in DB for internal evaluation.
- `min_confidence_for_publish` (default 70) acts as a hard floor for `GET /api/v1/signals`.

---

## 10. Paper Trading & Evaluation Specification (Planned)

### 10.1 Position lifecycle

```
Signal → Entry (next bar) → Position (OPEN) → {Stop / Target / Time / Reversal / Manual} → Position (CLOSED|STOPPED|EXPIRED)
```

- **Entry:** Next bar open after signal `generated_at + 1m` (avoid look-ahead).
- **Stop logic:** `atr_trailing` (default, `2 × ATR`), `fixed_pct`, `structure`.
- **Target logic:** `risk_reward` (default, `2R`), `take_profit_pct`, `trailing`, `time_based`, `signal_reversal`.
- **Fees & slippage:** Applied at entry AND exit, in basis points (default 10 bps fees, 5 bps slippage).
- **Position sizing:** `min(max_position_pct × equity, free_cash)`.

### 10.2 Required metrics (`EvaluationMetrics`)

| Category | Metric |
|---|---|
| Volume | `total_signals`, `total_positions`, `closed_positions`, `open_positions` |
| Win/loss | `winning_positions`, `losing_positions`, `win_rate`, `loss_rate` |
| Returns | `avg_return_pct`, `median_return_pct`, `max/min/std_return_pct` |
| Risk | `max_drawdown_pct`, `profit_factor`, `sharpe_ratio`, `sortino_ratio`, `calmar_ratio` |
| P/L | `total_pnl_usd`, `total_fees_usd`, `total_slippage_usd` |
| Holding | `avg_holding_hours`, `avg_r_multiple` |
| Breakdowns | `hit_rate_by_confidence`, `hit_rate_by_regime`, `hit_rate_by_signal_class` |
| Quality | `signal_decay_half_life_hours`, `sell_timing_quality_score`, MFE/MAE |

### 10.3 Decay & sell-timing analysis

- **`DecayTracker`:** Buckets closed positions by time-since-signal; fits an exponential decay model to compute `half_life_hours` and `r_squared`.
- **`SellTiming`:** Compares `exit_price` to `peak_price_after_entry` and `trough_price_after_entry`. Outputs `exit_efficiency_pct ∈ [0, 100]` and `held_too_long` / `exited_too_early` flags.

### 10.4 Reporting

- **Daily / weekly / monthly** JSON reports in `./reports`.
- **Window:** `evaluation.metrics.window_days = 30` rolling.
- **Min sample:** `min_trades_for_stats = 10` (no metrics below threshold).

---

## 11. API Specification (Planned)

Base path: `/api/v1`. All endpoints return JSON. API key auth via `Authorization: Bearer <key>` for protected routes.

| Method | Path | Auth | Returns | Description |
|---|---|---|---|---|
| GET | `/signals` | ✅ key | `List[Signal]` | Latest publishable (HIGH/EXTREME) signals |
| GET | `/signals/{signal_id}` | ✅ key | `Signal` | Full signal incl. `contributing_factors` & `provenance` |
| GET | `/signals/history` | ✅ key | `List[Signal]` | Paginated history with `?asset=`, `?since=`, `?band=` filters |
| GET | `/performance/summary` | ✅ key | `EvaluationMetrics` | Aggregate metrics for the rolling window |
| GET | `/performance/confidence-bands` | ✅ key | `Dict[band, metrics]` | Hit rate, avg return, count by band |
| GET | `/performance/regimes` | ✅ key | `Dict[regime, metrics]` | Performance split by market regime |
| GET | `/performance/strategies` | ✅ key | `Dict[class, metrics]` | Performance split by signal class |
| GET | `/health` | public | `{status, version, ts}` | Liveness/readiness |
| GET | `/providers/status` | ✅ key | `Dict[provider, status]` | Provider health snapshot |
| GET | `/metrics` | public | Prometheus exposition | Worker / API / DB metrics |

**Permissions (per-key):** `read:signals`, `read:performance`, `read:health`, `*` (admin).

---

## 12. CLI Specification (Planned)

Single entrypoint: `python -m signals_lab.cli.main <command> [subcommand]`.

| Command | Subcommand | Description |
|---|---|---|
| `ingest` | `start`, `once`, `status` | Manage ingestion scheduler |
| `features` | `compute`, `list`, `enable`, `disable` | Manage feature engine |
| `signals` | `generate`, `list`, `show`, `history` | Signal generation + inspection |
| `evaluate` | `run`, `report`, `decay`, `sell-timing` | Paper evaluation utilities |
| `api` | `serve`, `routes` | API server |
| `db` | `migrate`, `seed`, `reset` | Database utilities |
| `config` | `show`, `validate` | Inspect active config |

---

## 13. Quality Gates & Tooling

Run **before** every commit / PR:

```bash
ruff check src/ tests/                # Lint
ruff format --check src/ tests/        # Format check
mypy src/signals_lab                   # Type check
pytest -m unit --cov=src/signals_lab   # Unit tests with coverage
```

CI is configured to **block merges** on:
- Any `ruff` error
- Any `mypy` error
- Coverage < **80%** on touched lines
- Any failing test (including async)

`pyproject.toml` is the single source of truth for `ruff`, `mypy`, `black`, `isort`, `pytest`, `coverage` configuration.

---

## 14. Milestones (from ARCHITECTURE.md, restated for tracking)

### Stage 1 — Foundation ✅ ~80%
- ✅ Project setup (pyproject, config, logging, structure)
- ✅ Domain models (enums + signals + features + evaluation Pydantic schemas)
- ✅ Storage abstraction (TimescaleDB hypertables, relational client)
- ✅ Configuration system (YAML + env overlay, frozen Pydantic settings)
- ✅ Ingestion skeletons (base, market/social/onchain/event, scheduler)
- ⏳ Database migrations (alembic setup)
- ⏳ Unit tests for domain + storage

### Stage 2 — Feature Engine + Basic Signals
- [ ] Feature registry + engine orchestration
- [ ] Trend / Momentum / Mean-reversion / Volatility families
- [ ] Social / Onchain / Event feature stubs
- [ ] Signal rule engine (config-driven)
- [ ] Ranking + confidence calibration
- [ ] Provenance tracking

### Stage 3 — Paper Evaluator + API Publishing
- [ ] Paper trader (fees, slippage, position sizing)
- [ ] Position lifecycle + state machine
- [ ] Metrics calculator (all required metrics)
- [ ] Decay + sell-timing analysis
- [ ] FastAPI app + all endpoints
- [ ] API auth + rate limiting
- [ ] Integration tests

### Stage 4 — Calibration + Comparative Analytics
- [ ] Confidence calibration using historical outcomes
- [ ] Comparative analytics (HIGH vs MEDIUM/LOW)
- [ ] Source attribution (does social add value?)
- [ ] Regime-dependent analysis
- [ ] Reporting dashboard

### Stage 5 — ML / Ranking Upgrades
- [ ] Gradient-boosted ranking model
- [ ] Feature importance analysis
- [ ] AutoML for feature selection
- [ ] Online learning for calibration
- [ ] Ensemble methods

---

## 15. Risks & Mitigations (Spec-level)

| Risk | Impact | Mitigation in spec |
|---|---|---|
| Provider API drift | High | Abstract behind `BaseProvider`; ship `Mock*Provider` fixtures |
| Look-ahead bias | **Critical** | All features use only `time ≤ t` data; enforced in feature engine tests |
| Signal overfitting | High | Walk-forward validation; rule versioning; out-of-sample backtest framework |
| TimescaleDB scaling | Medium | Hypertables auto-partition; `symbol`+`time` indexes; archival policy in `worker_runs` |
| API rate limits | Medium | Token-bucket per provider; exponential backoff; provider rotation |
| Confidence miscalibration | High | Bands defined in YAML; post-hoc calibration in Stage 4 |
| Schema drift between domain & DB | Medium | All DB writes serialize via Pydantic `.model_dump(mode="json")`; integration tests assert round-trip |
| Worker crash losing in-flight data | Medium | Per-batch transactions in `store_batch`; idempotency via unique constraint |

---

## 16. Definition of Done (per change)

A change to this codebase is **done** when:

1. ✅ Code is in the right module per Section 3.
2. ✅ Domain models touched are in `src/signals_lab/domain/` and remain **pure** (no I/O).
3. ✅ I/O is in `src/signals_lab/storage/` or `src/signals_lab/ingestion/`; no DB/HTTP calls elsewhere.
4. ✅ Pydantic invariants from Section 4 are respected.
5. ✅ Config changes go through `config/settings.yaml` + `SIGNALSLAB_*` env vars (Section 6).
6. ✅ New dependency → added to `pyproject.toml` with rationale in commit message.
7. ✅ Lint, format, mypy, and tests all pass (Section 13).
8. ✅ README.md / SPECS.md / AGENTS.md are updated if public surface area changes.
9. ✅ Unit tests added for new domain logic; integration tests for new I/O.
10. ✅ `git log` commit message includes a one-line summary + bullet refs to SPECS sections touched.

---

## 17. Open Spec Questions / TODO

These are intentional gaps in the current spec that the next iteration should resolve:

- [ ] Concrete API key hashing algorithm for `api_keys` table (Argon2id vs bcrypt).
- [ ] Exact JSONB schema for `signal_rules.conditions` (predicate tree grammar).
- [ ] `provenance` `rule_version` strategy when multiple rules fire (vote? first? highest weight?).
- [ ] Sliding-window vs tumbling-window for feature computation.
- [ ] Multi-tenant API key strategy (currently single tenant: iHabibi).
- [ ] Backfill semantics: does `IngestionScheduler.run_once()` accept a `(start, end)` range?
- [ ] Cold-start behavior when `min_data_points` not yet met for an asset.

---

*End of SPECS.md — see [AGENTS.md](./AGENTS.md) for AI-agent-specific guidance and [ARCHITECTURE.md](./ARCHITECTURE.md) for high-level design.*
