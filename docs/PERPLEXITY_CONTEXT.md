# signals-lab — Unified Context for Perplexity Pro (Strategic Brain)

> **Generated:** 2026-06-06 20:23 UTC · **Version:** 0.1.0 · **Regenerate:** `bin/signals-lab context export`
>
> Upload this file to your Perplexity Pro **Space** named `signals-lab`.
> Pair with `docs/PERPLEXITY_SPACE_INSTRUCTIONS.md` as Space custom instructions.

---

## 0. How to use this document (Perplexity = main brain)

**Division of labor**

| Tool | Role | Strengths |
|---|---|---|
| **Perplexity Pro** | Strategic brain | Market research, UX patterns, reliability architecture, latency budgets, competitive analysis, API/feeder design for future algo platform, prompt drafting |
| **Cursor / codebase** | Implementation | Python, tests, SPECS compliance, no-look-ahead enforcement, storage, workers |
| **signals-lab runtime** | Truth | Paper signals, metrics, health checks, provenance |

When answering, Perplexity should:
1. Ground recommendations in sections below (not generic crypto bot advice).
2. Tag every recommendation: `[MVP]` `[Stage 3]` `[Stage 4]` `[Future algo feeder]`.
3. Split **internal researcher UX** vs **downstream algo/iHabibi consumer UX**.
4. Never propose live order placement **inside signals-lab** (research boundary).
5. Propose **feeder contracts** (JSON/WebSocket) that a **separate** mini algo platform could consume later.

---

## 1. North star (reliability + speed + future feeder)

Build a **highly reliable, fast, explainable signal factory** that:

- Produces **confidence-calibrated** LONG/SHORT/WATCH candidates from multi-source data
- Publishes only **HIGH / EXTREME** bands to downstream consumers
- Tracks **paper-traded** outcomes with full provenance (reproducible, auditable)
- Serves as a **feeder layer** for a future **mini algo trading platform** (separate system)

**Reliability pillars (design for these):**
- Zero look-ahead bias (features at `t` use only data with `time ≤ t`)
- Rule + feature **versioning** on every signal (`computation_version`, `rule_version`)
- **Health checks** before ingestion (`signals-lab health apis|db`)
- **Publish gate** — LOW/MEDIUM never leak to external API
- **Cooldown** — no duplicate signals per asset within 4h
- **Walk-forward / out-of-sample** evaluation before promoting rules

**Speed targets (current config, tunable):**

| Stage | Target cadence | Notes |
|---|---|---|
| Market ingest | 60s | Binance REST/WS; fastest path to fresh OHLCV |
| Feature compute | every 15 min | `workers.features.schedule_cron` |
| Signal generate | every 5 min | `workers.signals.schedule_cron` |
| API poll (downstream) | 30–60s | Consumer-side; design for ETag + `since=` cursor |
| Future feeder | <1s push | NATS/WebSocket fan-out when `events.enabled` |

**Future mini algo platform (feeder, not executor here):**
- signals-lab exposes: signal ID, side, confidence, entry reference, stops, invalidation, expiry, provenance
- Downstream algo decides sizing, execution, risk — **outside** this repo
- Design API for **idempotent signal delivery** and **at-least-once** consumption

---

## 2. Mission & non-goals

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


**Non-goals (hard):**
- ❌ No live trading, exchange orders, or custody in signals-lab
- ❌ No look-ahead in features or paper eval
- ❌ No bypass of HIGH/EXTREME publish gate for external consumers

---

## 3. Architecture overview

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


**Pipeline (target state):**

```
Ingestion → TimescaleDB → FeatureEngine → RuleEngine → Ranking → ConfidenceCalibrator
    → Signals DB → PaperTrader → Metrics → FastAPI (+ optional NATS feeder)
```

---

## 4. What exists today (implementation truth)

### Module map

| Module | Status |
|---|---|
| `domain/` | implemented (alpha) |
| `features/` | implemented (alpha) |
| `ingestion/` | implemented (alpha) |
| `signals/` | implemented (alpha) |
| `storage/` | implemented (alpha) |
| `utils/` | partial (logging, health, context export) |


### Feature engine (implemented)

| Feature | Family | Function |
|---|---|---|
| `adx_14` | trend | adx |
| `atr_14` | volatility | atr |
| `bb_pct_b_20` | mean_reversion | bollinger_pct_b |
| `ema_12` | trend | ema |
| `ema_26` | trend | ema |
| `ema_50` | trend | ema |
| `macd_histogram` | momentum | macd |
| `realized_vol_20` | volatility | realized_vol |
| `roc_10` | momentum | roc |
| `rsi_14` | momentum | rsi |
| `sma_20` | trend | sma |
| `sma_200` | trend | sma |
| `sma_50` | trend | sma |
| `stochastic_k` | momentum | stochastic |
| `zscore_20` | mean_reversion | zscore |

**Total enabled:** 15


### Signal engine (partial)

| Component | Status |
|---|---|
| `RuleEngine` | ✅ Predicate tree evaluator, cooldown, regime gating |
| `ConfidenceCalibrator` | ✅ Maps score → band (LOW/MEDIUM/HIGH/EXTREME) |
| `RankingEngine` | ⬜ Planned |
| `SignalEngine` orchestration | ⬜ Planned |
| FastAPI publish layer | ⬜ Planned |

### CLI (implemented)

```text
signals-lab — Crypto Signal Research Platform (CLI wrapper)
=========================================================

signals-lab ingests crypto market, social, on-chain, and event data;
computes technical features; generates explainable, confidence-calibrated
paper-trading signals; and (when complete) exposes HIGH/EXTREME signals via
FastAPI to downstream consumers like iHabibi Trading.

  ⚠  This is NOT a live trading system. No exchange orders are placed.

Workflow
--------
  setup          Create venv and install dependencies  (./setup.sh)
  config         Inspect or validate configuration
  ingest         Fetch data from providers → TimescaleDB
  features       Compute technical features from observations
  signals        Generate ranked, confidence-calibrated signals
  evaluate       Paper-trade signals and compute performance metrics
  api            Serve the FastAPI publishing layer
  db             Database migrations and utilities
  test           Run the test suite
  lint           Run ruff linter / formatter
  typecheck      Run mypy on src/signals_lab
  check          Run lint + typecheck + unit tests (quality gates)
  health         Test API keys, providers, RSS feeds, and databases
  context        Export unified spec for Perplexity Pro / external LLMs
  version        Show package version

Commands
--------
  setup                  [available] ./setup.sh — venv + all dependencies
  config show            [available] Print active settings summary
  config validate        [available] Validate settings.yaml loads cleanly
  features list          [available] List registered feature definitions
  features compute       [available] Demo feature computation (synthetic data)
  ingest once            [available] Single fetch cycle (needs PostgreSQL + keys)
  ingest start           [available] Start continuous ingestion loop (needs DB)
  ingest status          [available] Show configured ingestors and intervals
  test [args]            [available] pytest -m unit (pass extra args through)
  lint [check|fix]       [available] ruff check / format
  typecheck              [available] mypy src/signals_lab
  check                  [available] lint + typecheck + unit tests
  health [apis|db]       [available] Test API keys, RSS feeds, databases
  api health             [available] External API connectivity only
  context export         [available] Build docs/PERPLEXITY_CONTEXT.md for Perplexity Pro
  version                [available] Print version string

Planned (not yet wired — use python -m signals_lab.cli.main when available):
  signals generate       [planned]   Run signal engine on latest features
  signals list           [planned]   List recent signals from DB
  evaluate run           [planned]   Paper-trade open signals
  evaluate report        [planned]   Generate performance report
  api serve              [planned]   Start uvicorn FastAPI server
  db migrate             [planned]   Run Alembic migrations
  db seed                [planned]   Seed feature rules and registry

Examples
  ./setup.sh                          # first-time bootstrap (recommended)
  export PATH="$(pwd)/bin:$PATH"      # then use signals-lab anywhere
  signals-lab config show
  signals-lab features compute        # no database needed
  signals-lab check                   # lint + tests
  signals-lab health                  # test APIs + DB
  signals-lab health apis             # APIs/RSS only (no DB required)
  signals-lab context export          # Perplexity Pro unified spec
  signals-lab ingest once             # needs PostgreSQL/TimescaleDB
  signals-lab help ingest

Environment
  Copy .env.example → .env and set API keys (LunarCrush, NewsAPI, etc.).
  Config file: config/settings.yaml (overridable via SIGNALSLAB_* env vars).

Docs: README.md · ARCHITECTURE.md · SPECS.md · AGENTS.md · docs/PERPLEXITY_SPACE_INSTRUCTIONS.md
```

### Health checks (implemented)

`signals-lab health apis` — Binance, NewsAPI, LunarCrush, RSS, DB connectivity

---

## 5. Active configuration snapshot

```yaml
app:
  environment: development
ingestion:
  market: enabled=True, interval=60s
  social: enabled=True, interval=300s
  onchain: enabled=False, interval=900s
  events: enabled=True, interval=300s
features:
  windows: ['1h', '4h', '1d']
  lookback_periods: 500
  min_data_points: 50
signals:
  min_confidence_for_publish: 70.0
  signal_cooldown_hours: 4
workers:
  features_cron: */15 * * * *
  signals_cron: */5 * * * *
  evaluation_cron: 0 * * * *
api:
  prefix: /api/v1
  port: 8000
```

---

## 6. Signal pipeline spec (from SPECS)

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



### Publishing rule

- External API: **HIGH + EXTREME only**
- `min_confidence_for_publish` default **70**
- Every signal carries `thesis`, `contributing_factors`, `invalidation_condition`, `provenance`

---

## 7. Planned API (downstream / algo feeder)

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


**Algo feeder requirements (propose designs for these):**
- Stable `signal_id` (UUID), monotonic `generated_at`
- `confidence_band` + numeric `confidence_score`
- `side`, `signal_class`, `regime`
- `suggested_stop`, `suggested_sell`, `expected_holding_horizon`
- `provenance.rule_version`, `provenance.data_sources`
- Pagination: `GET /signals/history?since=&asset=`
- Optional push: NATS topic `signals.generated.>` (disabled by default)

---

## 8. Milestones

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


---

## 9. Data providers (cost / reliability)

| Provider | Role | Cost | Status |
|---|---|---|---|
| Binance | Market OHLCV | Free | ✅ Implemented |
| NewsAPI.org | Events/news | Free dev tier | Configured; ingest mock |
| CoinDesk/CoinTelegraph RSS | Events | Free | Health-checked |
| LunarCrush | Social sentiment | Paid | Key optional; HTTP 402 = upgrade needed |
| Glassnode | On-chain | Paid | Disabled by default |
| CryptoPanic | Events | Paid | Deprioritized |

---

## 10. Personas (always specify in prompts)

1. **Researcher** — runs CLI, tunes rules, reads paper eval metrics
2. **iHabibi / dashboard consumer** — polls API, shows signal cards to humans
3. **Mini algo platform (future)** — automated feeder consumer; needs low-latency, idempotent, structured JSON

---

## 11. Open questions for Perplexity to resolve

1. Optimal **UX** for explaining confidence bands + contributing factors to semi-technical users?
2. **Latency architecture**: 5-min signal cron vs event-driven (bar close WebSocket trigger)?
3. **Reliability**: what SLAs and circuit-breakers for a feeder used by algo trading?
4. **MVP API schema** for algo consumer — minimum fields for safe paper → live handoff (in downstream system)?
5. **Feature set** for fast intraday signals vs slower swing signals — tradeoffs?
6. **Competitive patterns** from TradingView, 3Commas, Nansen, Messari — what to adopt/avoid?

---

## 12. Prompt template (paste into Perplexity thread)

```
Context: uploaded signals-lab unified spec.
Persona: [Researcher | iHabibi dashboard | Mini algo feeder]
Goal: [one sentence]
Constraints: no live trading in signals-lab; HIGH/EXTREME publish only; no look-ahead.

Deliver:
1. Recommendation (tag MVP / Stage 3 / Future feeder)
2. UX or API sketch
3. Reliability & latency notes
4. What to implement in Cursor next (files/modules)
5. Risks & mitigations
```

---

## 13. README excerpt

# signals-lab

High-performance crypto market signal research platform.

**signals-lab** is a research-grade platform that:
- Ingests market, social, sentiment, on-chain, and event/geopolitical data
- Computes reusable research features
- Generates ranked buy/sell/watch signals with explainable confidence scores
- Tracks paper outcomes and P/L over time
- Exposes approved signals and performance metrics through an API for [iHabibi Trading](https://ihabibi.com)

> **⚠️ This is NOT a live trading system.** It performs research, paper evaluation, and signal publishing only. No exchange orders are placed.

## Architecture

```
Ingestion Workers → Time-Series Storage → Feature Engine → Signal Engine → (Paper Evaluator + Publisher API)
```

- **Ingestion**: Market (Binance), Social (LunarCrush), On-Chain (Glassnode), Events (NewsAPI)
- **Features**: Trend, momentum, mean reversion, volatility, social, on-chain, events, cross-asset
- **Signals**: Confidence-calibrated (low/medium/high/extreme), only high/extreme published
- **Evaluation**: Full paper trading with win rate, expectancy, profit factor, decay analysis
- **API**: FastAPI with signal publishing, performance metrics, health checks

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design document.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL with TimescaleDB extension (for time-series data)
- API keys for data providers (optional - mock providers included)

### Setup

```bash
# Clone the repository
git clone git@github.com:chessz/ihabibi-signal-labs.git
cd ihabibi-signal-labs


---

*End of unified context — regenerate after major milestones.*
