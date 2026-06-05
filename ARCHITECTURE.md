# signals-lab Architecture Document

## Mission
High-performance signal research platform for crypto markets that:
- Ingests market, social, sentiment, on-chain, and event/geopolitical data
- Computes reusable research features
- Generates ranked buy/sell/watch signals with confidence scores
- Tracks paper outcomes and P/L over time
- Exposes approved signals and performance metrics through an API for iHabibi Trading

---

## 1. Folder Structure

```
signals-lab/
├── .github/
│   └── workflows/           # CI/CD pipelines
├── config/
│   ├── settings.yaml        # Main configuration
│   ├── providers.yaml       # Data provider configurations
│   ├── features.yaml        # Feature definitions and parameters
│   └── signals.yaml         # Signal rule definitions
├── docs/
│   ├── architecture.md      # This file
│   ├── api.md              # API documentation
│   ├── data-model.md       # Domain model documentation
│   └── evaluation.md       # Evaluation methodology
├── scripts/
│   ├── migrate.py          # Database migrations
│   ├── seed.py             # Seed data
│   └── dev-setup.sh        # Development environment setup
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test data fixtures
├── src/
│   ├── signals_lab/        # Main package
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration loading
│   │   ├── domain/         # Domain models (entities, value objects)
│   │   │   ├── __init__.py
│   │   │   ├── market.py
│   │   │   ├── social.py
│   │   │   ├── onchain.py
│   │   │   ├── events.py
│   │   │   ├── features.py
│   │   │   ├── signals.py
│   │   │   ├── evaluation.py
│   │   │   └── enums.py
│   │   ├── storage/        # Storage abstraction layer
│   │   │   ├── __init__.py
│   │   │   ├── timeseries.py   # Time-series storage (InfluxDB/TimescaleDB)
│   │   │   ├── relational.py   # Relational storage (PostgreSQL)
│   │   │   ├── repository.py   # Repository pattern implementations
│   │   │   └── migrations/     # Database migrations
│   │   ├── ingestion/      # Data ingestion services
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── market_ingestor.py
│   │   │   ├── social_ingestor.py
│   │   │   ├── onchain_ingestor.py
│   │   │   ├── event_ingestor.py
│   │   │   └── scheduler.py
│   │   ├── features/       # Feature engineering engine
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   ├── registry.py
│   │   │   ├── families/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── trend.py
│   │   │   │   ├── momentum.py
│   │   │   │   ├── mean_reversion.py
│   │   │   │   ├── volatility.py
│   │   │   │   ├── social.py
│   │   │   │   ├── onchain.py
│   │   │   │   ├── events.py
│   │   │   │   └── cross_asset.py
│   │   │   └── computed/   # Computed feature storage
│   │   ├── signals/        # Signal generation engine
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   ├── rules.py
│   │   │   ├── ranking.py
│   │   │   ├── confidence.py
│   │   │   └── provenance.py
│   │   ├── evaluation/     # Paper trading evaluation
│   │   │   ├── __init__.py
│   │   │   ├── paper_trader.py
│   │   │   ├── metrics.py
│   │   │   ├── tracker.py
│   │   │   ├── decay.py
│   │   │   └── reporting.py
│   │   ├── api/            # FastAPI application
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── signals.py
│   │   │   │   ├── performance.py
│   │   │   │   ├── health.py
│   │   │   │   └── providers.py
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── signals.py
│   │   │   │   ├── performance.py
│   │   │   │   └── health.py
│   │   │   ├── dependencies.py
│   │   │   └── middleware.py
│   │   ├── workers/        # Background workers
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── ingestion_worker.py
│   │   │   ├── feature_worker.py
│   │   │   ├── signal_worker.py
│   │   │   └── evaluation_worker.py
│   │   ├── events/         # Event bus (optional NATS)
│   │   │   ├── __init__.py
│   │   │   ├── bus.py
│   │   │   ├── topics.py
│   │   │   └── handlers.py
│   │   └── utils/          # Shared utilities
│   │       ├── __init__.py
│   │       ├── datetime.py
│   │       ├── math.py
│   │       └── logging.py
│   └── cli/                # Command-line interface
│       ├── __init__.py
│       ├── main.py
│       └── commands/
├── pyproject.toml          # Project configuration
├── poetry.lock             # Locked dependencies
├── README.md
├── ARCHITECTURE.md
└── .env.example            # Example environment variables
```

---

## 2. Domain Model

### Core Enums

```python
# Signal Output Classes
class SignalClass(str, Enum):
    LONG_CANDIDATE = "long_candidate"
    SHORT_CANDIDATE = "short_candidate"
    WATCH_ONLY = "watch_only"
    IGNORE = "ignore"

# Confidence Bands
class ConfidenceBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

# Signal Side
class SignalSide(str, Enum):
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"

# Market Regime
class MarketRegime(str, Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"

# Data Source Types
class DataSourceType(str, Enum):
    MARKET = "market"
    ONCHAIN = "onchain"
    SOCIAL = "social"
    EVENTS = "events"
```

### Core Entities

#### AssetPair
```python
class AssetPair:
    symbol: str                    # e.g., "BTC/USDT"
    base: str                      # e.g., "BTC"
    quote: str                     # e.g., "USDT"
    exchange: str                  # e.g., "binance"
    is_active: bool
    metadata: dict
```

#### MarketObservation (Time-Series)
```python
class MarketObservation:
    asset_pair: AssetPair
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    spread_bps: Optional[int]      # Spread in basis points
    realized_volatility: Optional[Decimal]
    funding_rate: Optional[Decimal] # For perpetuals
    open_interest: Optional[Decimal]
    source: str                    # Provider identifier
```

#### SocialObservation (Time-Series)
```python
class SocialObservation:
    asset_pair: AssetPair
    timestamp: datetime
    mention_count: int
    sentiment_score: Decimal       # -1 to 1
    sentiment_positive: int
    sentiment_negative: int
    sentiment_neutral: int
    influencer_mentions: int
    social_dominance_pct: Decimal  # % of total crypto mentions
    topic_tags: List[str]
    source: str
```

#### OnChainObservation (Time-Series)
```python
class OnChainObservation:
    asset_pair: AssetPair
    timestamp: datetime
    exchange_inflow_usd: Decimal
    exchange_outflow_usd: Decimal
    whale_transaction_count: int
    whale_transaction_volume_usd: Decimal
    stablecoin_minted_usd: Decimal
    stablecoin_redeemed_usd: Decimal
    supply_on_exchanges_pct: Decimal
    large_holder_net_flow_usd: Decimal
    source: str
```

#### EventObservation (Time-Series)
```python
class EventObservation:
    timestamp: datetime
    event_type: str                # regulatory, etf, exchange_incident, geopolitical, macro
    title: str
    description: str
    severity: int                  # 1-5
    affected_assets: List[str]
    region: Optional[str]
    country_sentiment: Optional[Decimal]  # -1 to 1
    market_impact_estimate: Optional[Decimal]
    tags: List[str]
    source: str
    url: Optional[str]
```

#### FeatureVector (Computed)
```python
class FeatureVector:
    asset_pair: AssetPair
    timestamp: datetime
    feature_family: str            # trend, momentum, mean_reversion, etc.
    feature_name: str
    value: Decimal
    window: str                    # e.g., "1h", "4h", "1d"
    computation_version: str
```

#### Signal (Core Output)
```python
class Signal:
    signal_id: UUID
    asset_pair: AssetPair
    signal_class: SignalClass
    side: SignalSide
    confidence_score: Decimal      # 0-100
    confidence_band: ConfidenceBand
    generated_at: datetime
    expiry_at: datetime
    regime: MarketRegime
    thesis: str                    # Human-readable explanation
    contributing_factors: List[ContributingFactor]
    invalidation_condition: str
    suggested_stop: Optional[StopLogic]
    suggested_sell: Optional[SellLogic]
    expected_holding_horizon: str  # e.g., "4h", "1d", "1w"
    provenance: ProvenanceRecord
    status: SignalStatus           # active, expired, invalidated, filled_paper
```

#### ContributingFactor
```python
class ContributingFactor:
    feature_family: str
    feature_name: str
    value: Decimal
    weight: Decimal                # Contribution to confidence
    direction: str                 # "bullish", "bearish", "neutral"
    description: str
```

#### ProvenanceRecord
```python
class ProvenanceRecord:
    data_sources: List[str]        # Provider names
    observation_window: str        # e.g., "last 24h"
    computation_version: str
    rule_version: str
    generated_by: str              # Worker/service identifier
```

#### StopLogic / SellLogic
```python
class StopLogic:
    type: str                      # "fixed_pct", "atr_trailing", "structure"
    value: Decimal
    reference_price: Decimal

class SellLogic:
    type: str                      # "take_profit_pct", "trailing", "time_based", "signal_reversal"
    value: Decimal
    reference_price: Decimal
```

#### PaperPosition (Evaluation)
```python
class PaperPosition:
    position_id: UUID
    signal_id: UUID
    asset_pair: AssetPair
    side: SignalSide
    entry_price: Decimal
    entry_time: datetime
    quantity: Decimal
    stop_price: Optional[Decimal]
    target_price: Optional[Decimal]
    status: PositionStatus         # open, closed, stopped, expired
    exit_price: Optional[Decimal]
    exit_time: Optional[datetime]
    exit_reason: Optional[str]
    pnl_usd: Optional[Decimal]
    pnl_pct: Optional[Decimal]
    fees_usd: Decimal
    slippage_usd: Decimal
    max_favorable_excursion_pct: Optional[Decimal]
    max_adverse_excursion_pct: Optional[Decimal]
    holding_period_hours: Optional[Decimal]
```

#### EvaluationMetrics (Aggregated)
```python
class EvaluationMetrics:
    period_start: datetime
    period_end: datetime
    total_signals: int
    total_positions: int
    win_rate: Decimal
    loss_rate: Decimal
    expectancy: Decimal
    avg_return_pct: Decimal
    median_return_pct: Decimal
    max_drawdown_pct: Decimal
    profit_factor: Decimal
    sharpe_ratio: Optional[Decimal]
    hit_rate_by_confidence: Dict[ConfidenceBand, Decimal]
    hit_rate_by_regime: Dict[MarketRegime, Decimal]
    hit_rate_by_signal_class: Dict[SignalClass, Decimal]
    signal_decay_half_life_hours: Decimal
    sell_timing_quality_score: Decimal
```

---

## 3. Storage Design

### Time-Series Storage (InfluxDB or TimescaleDB)
**High-volume, high-ingestion data:**
- `market_observations` - OHLCV, spread, volatility, funding, OI
- `social_observations` - Mentions, sentiment, dominance, topics
- `onchain_observations` - Flows, whale activity, stablecoins, supply
- `event_observations` - Headlines, severity, impact estimates
- `feature_vectors` - Computed feature values per asset/window

**Schema pattern:**
```
measurement: market_observations
tags: asset_pair, exchange, source
fields: open, high, low, close, volume, spread_bps, realized_vol, funding_rate, open_interest
timestamp: observation time
```

### Relational Storage (PostgreSQL)
**Metadata, configuration, signals, evaluation:**
- `asset_pairs` - Trading pairs, exchange mappings
- `providers` - Data provider configs, credentials (encrypted), status
- `signals` - Generated signals with full details
- `paper_positions` - Paper trading positions
- `evaluation_metrics` - Aggregated performance metrics
- `signal_rules` - Versioned signal generation rules
- `feature_registry` - Feature definitions and parameters
- `worker_runs` - Worker execution logs
- `api_keys` - Downstream consumer API keys

### Storage Abstraction
Repository pattern with interfaces:
- `TimeSeriesRepository` - Write/read time-series data
- `RelationalRepository` - CRUD for entities
- `FeatureRepository` - Feature vector storage/retrieval
- `SignalRepository` - Signal persistence and querying
- `EvaluationRepository` - Position and metrics storage

---

## 4. Service Boundaries

### Ingestion Services (Independent Workers)
| Service | Responsibility | Frequency |
|---------|---------------|-----------|
| `market_ingestor` | Fetch OHLCV, order book snapshots, funding, OI from exchanges | 1m - 5m |
| `social_ingestor` | Fetch mentions, sentiment from LunarCrush, Twitter API, Reddit, etc. | 5m - 15m |
| `onchain_ingestor` | Fetch exchange flows, whale alerts, stablecoin data from Glassnode, Nansen, etc. | 15m - 1h |
| `event_ingestor` | Fetch news, regulatory, geopolitical events from news APIs | 5m - 30m |

**Shared:** `IngestionScheduler` - Coordinates scheduling, handles rate limits, retries

### Feature Engine
- **`FeatureEngine`** - Orchestrates feature computation
- **`FeatureRegistry`** - Manages feature definitions, versions, dependencies
- **Feature Families** (pluggable modules):
  - `trend` - Moving averages, ADX, parabolic SAR
  - `momentum` - RSI, MACD, rate of change, stochastic
  - `mean_reversion` - Bollinger bands, z-score, RSI extremes
  - `volatility` - ATR, realized vol, vol regime, expansion/contraction
  - `social` - Mention velocity, sentiment divergence, dominance shifts
  - `onchain` - Flow imbalance, whale net flow, supply concentration
  - `events` - Event risk penalty, catalyst proximity
  - `cross_asset` - Correlation, beta to BTC/ETH, sector rotation

### Signal Engine
- **`SignalEngine`** - Main orchestration
- **`RuleEngine`** - Evaluates signal rules (configurable, versioned)
- **`RankingEngine`** - Ranks candidates by composite score
- **`ConfidenceCalibrator`** - Maps raw scores to calibrated confidence bands
- **`ProvenanceTracker`** - Records data lineage for each signal

**Signal Generation Flow:**
```
Feature Vectors → Rule Evaluation → Candidate Signals → Ranking → Confidence Calibration → Output Signals
```

### Paper Evaluator
- **`PaperTrader`** - Simulates position entry/exit based on signals
- **`MetricsCalculator`** - Computes all evaluation metrics
- **`DecayTracker`** - Measures signal decay over time
- **`ReportGenerator`** - Produces evaluation reports

### Event Bus (Optional - NATS)
**Topics:**
- `market.observations.*` - New market data
- `social.observations.*` - New social data
- `onchain.observations.*` - New on-chain data
- `events.observations.*` - New events
- `features.computed.*` - Features ready
- `signals.generated.*` - New signals
- `evaluation.position_update.*` - Position P&L updates

**Benefits:** Decouples ingestion → features → signals → evaluation, enables replay, supports horizontal scaling

### Publisher API (FastAPI)
**Endpoints:**
```
GET  /api/v1/signals              # Latest published signals (high/extreme only)
GET  /api/v1/signals/{signal_id}  # Signal details with justification
GET  /api/v1/signals/history      # Historical signals with filters
GET  /api/v1/performance/summary  # Overall performance metrics
GET  /api/v1/performance/confidence-bands  # Stats by confidence band
GET  /api/v1/performance/regimes  # Stats by market regime
GET  /api/v1/performance/strategies  # Stats by signal family
GET  /api/v1/health               # Health check
GET  /api/v1/providers/status     # Data provider status
```

**Authentication:** API key based for iHabibi Trading integration

---

## 5. Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Exchanges  │     │  Social/    │     │  On-Chain   │
│  (REST/WS)  │     │  News APIs  │     │  Providers  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────┐
│                  INGESTION WORKERS                   │
│  Market │ Social │ OnChain │ Event  (parallel)      │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                 TIME-SERIES STORAGE                  │
│   (InfluxDB/TimescaleDB - High write throughput)    │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   FEATURE ENGINE                     │
│  Computes feature vectors per asset/window          │
│  Stores in feature_vectors measurement              │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   SIGNAL ENGINE                      │
│  Rule evaluation → Ranking → Confidence calibration │
│  Outputs to signals table (PostgreSQL)              │
└────────────────────────┬────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
    ┌─────────────────┐    ┌─────────────────┐
    │ PAPER EVALUATOR │    │  PUBLISHER API  │
    │ - Simulates     │    │ - Serves        │
    │ - Tracks P/L    │    │   high/extreme  │
    │ - Computes      │    │   signals       │
    │   metrics       │    │ - Performance   │
    └─────────────────┘    └─────────────────┘
```

---

## 6. Initial Milestones

### Stage 1: Foundation (Week 1-2)
- [ ] Project setup: poetry, config, logging, base structures
- [ ] Domain models (enums, entities) with Pydantic
- [ ] Storage abstraction: TimescaleDB + PostgreSQL repositories
- [ ] Database migrations (schema creation)
- [ ] Configuration system (YAML + env vars)
- [ ] Ingestion skeletons: base classes, scheduler, mock providers
- [ ] Unit tests for domain models and repositories

### Stage 2: Feature Engine + Basic Signals (Week 3-4)
- [ ] Feature registry and engine orchestration
- [ ] Implement core feature families:
  - [ ] Trend (SMA, EMA, ADX)
  - [ ] Momentum (RSI, MACD, ROC)
  - [ ] Mean Reversion (Bollinger, Z-score)
  - [ ] Volatility (ATR, Realized Vol)
- [ ] Social/Onchain/Event feature stubs
- [ ] Signal rule engine (config-driven)
- [ ] Basic ranking and confidence calibration
- [ ] Provenance tracking

### Stage 3: Paper Evaluator + API Publishing (Week 5-6)
- [ ] Paper trader with fee/slippage modeling
- [ ] Position lifecycle management
- [ ] Metrics calculator (all required metrics)
- [ ] Decay tracking and sell timing quality
- [ ] FastAPI application with all endpoints
- [ ] API authentication and rate limiting
- [ ] Integration tests for API

### Stage 4: Confidence Calibration + Comparative Analytics (Week 7-8)
- [ ] Confidence calibration using historical outcomes
- [ ] Comparative analytics: high vs medium/low confidence
- [ ] Source attribution analysis (does social add value?)
- [ ] Regime-dependent performance analysis
- [ ] Automated reporting dashboard

### Stage 5: ML/Ranking Upgrades (Future)
- [ ] ML-based signal ranking (gradient boosting, etc.)
- [ ] Feature importance analysis
- [ ] AutoML for feature selection
- [ ] Online learning for confidence calibration
- [ ] Ensemble methods for signal combination

---

## 7. Risks and Assumptions

### Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Data provider API changes | High | Abstract providers behind interfaces, mock for tests |
| TimescaleDB/PostgreSQL scaling | Medium | Design for partitioning, read replicas |
| Signal overfitting | High | Strict out-of-sample evaluation, walk-forward validation |
| Look-ahead bias in features | Critical | Feature computation uses only data available at timestamp |
| API rate limits | Medium | Exponential backoff, provider rotation, caching |

### Assumptions
1. **No live trading** - This is a research platform only
2. **Paper trading assumptions** - Fixed fee bps, slippage model configurable
3. **Data availability** - Initial phase uses free/public APIs; paid providers later
4. **Compute resources** - Single-node development, horizontal scaling later
5. **Team size** - Small team (1-3 engineers), favor simplicity over premature optimization

---

## 8. Technology Choices

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Rich data science ecosystem, FastAPI, async support |
| API Framework | FastAPI | High performance, auto-docs, type safety |
| Time-Series DB | TimescaleDB | PostgreSQL compatible, automatic partitioning, SQL queries |
| Relational DB | PostgreSQL | ACID, JSONB, mature ecosystem |
| Config | Pydantic Settings + YAML | Type-safe, environment-aware |
| Validation | Pydantic v2 | Fast, strict, integrates with FastAPI |
| Testing | pytest + pytest-asyncio | Standard, async support |
| Linting | ruff | Fast, comprehensive |
| Type Checking | mypy | Catch bugs early |
| Logging | structlog + loguru | Structured, contextual |
| Async | asyncio + aiohttp | Native Python, high concurrency |
| Scheduling | apscheduler | Flexible, persistent jobs |
| Metrics | prometheus-client | Observable, standard |

---

## 9. Configuration Example

```yaml
# config/settings.yaml
app:
  name: "signals-lab"
  environment: "development"
  log_level: "INFO"

storage:
  timeseries:
    url: "postgresql://user:pass@localhost:5432/signals_ts"
    pool_size: 10
  relational:
    url: "postgresql://user:pass@localhost:5432/signals_rel"
    pool_size: 10

ingestion:
  market:
    enabled: true
    interval_seconds: 60
    providers:
      - name: "binance"
        type: "rest"
        symbols: ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
  social:
    enabled: true
    interval_seconds: 300
    providers:
      - name: "lunarcrush"
        api_key_env: "LUNARCRUSH_API_KEY"
  onchain:
    enabled: false  # Enable when provider configured
    interval_seconds: 900
  events:
    enabled: true
    interval_seconds: 300
    providers:
      - name: "newsapi"
        api_key_env: "NEWSAPI_KEY"

features:
  computation_windows: ["1h", "4h", "1d"]
  lookback_periods: 500
  families:
    trend:
      enabled: true
      params:
        sma_periods: [20, 50, 200]
        ema_periods: [12, 26, 50]
        adx_period: 14
    momentum:
      enabled: true
      params:
        rsi_period: 14
        macd_fast: 12
        macd_slow: 26
        macd_signal: 9

signals:
  min_confidence_for_publish: 70  # high band threshold
  confidence_bands:
    low: [0, 40)
    medium: [40, 60)
    high: [60, 80)
    extreme: [80, 100]
  rule_version: "v1.0.0"

evaluation:
  paper_trading:
    fee_bps: 10
    slippage_bps: 5
    initial_capital_usd: 100000
    max_position_pct: 0.10
  metrics_window_days: 30

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  rate_limit: "100/minute"
  api_keys:
    - name: "ihabibi-trading"
      key_env: "IHABIBI_API_KEY"
      permissions: ["read:signals", "read:performance"]
```

---

## 10. Next Steps

**Immediate (this session):**
1. Create `pyproject.toml` with dependencies
2. Create folder structure
3. Implement domain models (`src/signals_lab/domain/`)
4. Create configuration system (`src/signals_lab/config.py`)
5. Create storage abstractions (`src/signals_lab/storage/`)
6. Create basic ingestion skeletons

**After foundation:**
1. Implement TimescaleDB migrations
2. Build feature engine with core families
3. Build signal engine with rule evaluation
4. Build paper evaluator
5. Build FastAPI application

---

*Document version: 1.0*
*Last updated: 2026-06-05*