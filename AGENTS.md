# AGENTS.md — Guidance for AI Coding Agents (Cursor, Claude Code, etc.)

> **Audience:** AI coding assistants working in this repository (Cursor, Claude Code, etc.)
> **Companion docs:** [README.md](./README.md) (overview), [ARCHITECTURE.md](./ARCHITECTURE.md) (high-level design), [SPECS.md](./SPECS.md) (technical specifications)
> **Last updated:** 2026-06-06
> **Project status:** Alpha (v0.1.0) — Stage 1/2 of a 5-stage plan is in progress

---

## 0. Read This First (TL;DR)

This is **signals-lab**, a Python 3.11+ async research platform that ingests crypto market/social/on-chain/event data, computes technical features, and generates **explainable, confidence-calibrated, paper-traded** crypto trading signals. It does **not** place live orders.

**The 5 non-negotiable rules:**

1. 🚫 **No live trading code.** Never add exchange-order placement, broker APIs, custody, or auto-execution.
2. 🧠 **No look-ahead bias.** Features/signals at time `t` must only use observations with `time ≤ t`.
3. 🧱 **Domain is pure.** `src/signals_lab/domain/*` is pure Pydantic. **Zero I/O, zero HTTP, zero DB.**
4. 🔌 **I/O lives in storage/ and ingestion/.** All DB and HTTP code stays in those two layers.
5. 📊 **Only HIGH/EXTREME signals are published.** All other bands stay in the DB for internal evaluation.

If a task appears to violate any of the above, **stop and ask the user** before writing any code.

---

## 1. Project Context

**What it is:** A research-grade platform that produces **paper-traded** crypto trading signals and exposes them to a downstream consumer (iHabibi Trading) via a FastAPI.

**What it is NOT:** A trading bot. A retail UI. A backtester UI. A custody system.

**Current state (as of 2026-06-06):**
- ✅ Stage 1 (Foundation) is ~80% complete: domain models, storage abstractions, config system, ingestion skeletons, scheduler.
- ⏳ Alembic migrations not yet wired up.
- 🚧 Stage 2 (Feature Engine + basic signals) just starting.
- ⬜ Stage 3 (Paper evaluator + API), Stage 4 (Calibration), Stage 5 (ML) all pending.

**Always check `[SPECS.md §14 Milestones](./SPECS.md#14-milestones-from-architecturemd-restated-for-tracking)` to know which stage you're working on.**

---

## 2. Tech Stack (frozen for now)

| Layer | Choice | Version pin |
|---|---|---|
| Python | 3.11+ | `requires-python = ">=3.11"` |
| Validation | Pydantic v2 | `>=2.7.0` |
| Settings | `pydantic-settings` | `>=2.3.0` |
| Async DB | `asyncpg` | `>=0.29.0` |
| ORM | SQLAlchemy 2.0 | `>=2.30` |
| Migrations | Alembic | `>=1.13.0` |
| HTTP | `aiohttp`, `httpx`, `websockets` | pinned in `pyproject.toml` |
| Time-series | TA-Lib + NumPy + pandas | pinned |
| Logging | `structlog` | `>=24.1.0` |
| Lint | `ruff` (rules: E, W, F, I, N, UP, B, C4, T20, SIM, ARG, PTH, ERA, PL) | `>=0.4.0` |
| Types | `mypy --strict` | `>=1.10.0` |
| Tests | `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"`) | pinned |

**Do not introduce new top-level dependencies** without a commit message that justifies it.

---

## 3. Where to Put New Code (Module Map)

```
src/signals_lab/
├── domain/          → PURE Pydantic. NO I/O. NO imports from storage/ingestion/api/features/signals.
│   ├── enums.py        # All enums live here.
│   ├── market.py       # AssetPair, MarketObservation
│   ├── social.py       # SocialObservation
│   ├── onchain.py      # OnChainObservation
│   ├── events.py       # EventObservation
│   ├── features.py     # FeatureDefinition, FeatureVector, FeatureBatch
│   ├── signals.py      # Signal, ContributingFactor, Stop/SellLogic, ProvenanceRecord, SignalRule, SignalCandidate, SignalOutputBatch
│   └── evaluation.py   # PaperPosition, EvaluationMetrics, DecayAnalysis, SellTimingMetrics, EvaluationReport
│
├── storage/         → The I/O boundary. DB code ONLY here.
│   ├── repository.py   # Abstract Repository classes (interfaces)
│   ├── timeseries.py   # TimescaleDBClient
│   └── relational.py   # PostgresRelationalClient
│
├── ingestion/       → External data acquisition. HTTP / WS / file parsing.
│   ├── base.py            # BaseProvider, BaseIngestor
│   ├── market_ingestor.py
│   ├── social_ingestor.py
│   ├── onchain_ingestor.py
│   ├── event_ingestor.py
│   └── scheduler.py       # IngestionScheduler
│
├── features/        → (planned) FeatureEngine, families/, registry
├── signals/         → (planned) SignalEngine, RuleEngine, ConfidenceCalibrator, Provenance
├── evaluation/      → (planned) PaperTrader, MetricsCalculator, DecayTracker, ReportGenerator
├── api/             → (planned) FastAPI app: routes, schemas, dependencies, middleware
├── workers/         → (planned) Long-running async workers (ingestion, feature, signal, eval)
├── events/          → (planned) Optional NATS bus: bus, topics, handlers
├── cli/             → (planned) Typer entrypoint
├── config.py        → Pydantic settings, get_settings(), YAML + env overlay. NO business logic.
└── utils/           → stateless helpers (datetime, logging, math)
```

**Decision rules:**

| If you are... | Put it in... |
|---|---|
| Adding a new domain entity or enum | `domain/<topic>.py` |
| Computing features from observations | `features/families/<family>.py` |
| Adding a new data provider (e.g. CryptoCompare) | `ingestion/<topic>_ingestor.py` (+ a `BaseProvider` subclass) |
| Adding a new DB table or repository method | `storage/relational.py` or `storage/timeseries.py` |
| Adding a new HTTP endpoint | `api/routes/<topic>.py` + `api/schemas/<topic>.py` |
| Adding a new scheduled job | `workers/<topic>_worker.py` |
| Adding a utility (no state) | `utils/<topic>.py` |
| Touching config (env / YAML) | `config.py` + `config/settings.yaml` |
| Writing a test | `tests/unit/...` (unit) or `tests/integration/...` (integration) |

---

## 4. Code Conventions

### 4.1 Style (enforced by ruff + black)

- **Line length:** 100 chars
- **Quotes:** double quotes
- **Indent:** 4 spaces, LF line endings
- **Import order:** stdlib → third-party → first-party (`signals_lab`) → local; enforced by `ruff.lint.isort`
- **Naming:**
  - Classes → `PascalCase`
  - Functions / methods / variables → `snake_case`
  - Constants → `UPPER_SNAKE`
  - Enums → `PascalCase` with `UPPER_SNAKE` members
  - Pydantic models → `PascalCase`, always inherit from `BaseModel`
  - Pydantic configs: `model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False, extra="forbid")` where appropriate

### 4.2 Type hints

- `mypy` is strict (`disallow_untyped_defs = true`, `disallow_incomplete_defs = true`).
- All public functions, methods, and class attributes must have type hints.
- Use `from __future__ import annotations` at the top of every module.
- Prefer `Optional[T]` over `T | None` for Pydantic compatibility unless target is 3.10+ only.
- Use `Decimal` for **all monetary and ratio values** (never `float`).
- Use `datetime` (timezone-aware, UTC) for **all timestamps**. Never `time.time()`.

### 4.3 Pydantic v2

- Always use `BaseModel` (v2 API), not v1-style `Config` classes.
- Validators: prefer `@field_validator` over v1 `@validator`.
- Serialization: use `.model_dump(mode="json")` (NOT `.dict()`) when persisting to JSONB.
- When forward-referencing another domain type, use `TYPE_CHECKING` + string annotation.

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from .market import AssetPair

class Signal(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    asset_pair: AssetPair
    confidence_score: Decimal = Field(..., ge=0, le=100)
```

### 4.4 Async / concurrency

- I/O-bound code: `async def` + `await`.
- CPU-bound (e.g. TA-Lib): prefer thread pool (`asyncio.to_thread`) or a process pool for large batches.
- One `asyncio.Task` per ingestor / worker. Use `asyncio.gather(..., return_exceptions=True)` to avoid cancellation cascades.
- Always use `async with` for connection acquisition; never `pool.acquire()` without a context manager.

### 4.5 Logging

- Use `structlog.get_logger(__name__)`.
- Bind context: `log = logger.bind(asset=symbol, ingestor=name)`.
- Event names: `snake_case` past-tense: `"fetch_cycle_complete"`, not `"completed fetch"`.
- Never use `print()` in `src/signals_lab/`. Use `logger.info(...)`. (`T201` is allowed only in `scripts/`.)

### 4.6 Error handling

- Domain code raises typed exceptions; let them propagate. Don't catch broad `Exception` in domain.
- I/O code catches and **logs** (with `exc_info=True`) the exception, then returns a safe default (e.g. `False`, empty list, `ProviderStatus.DOWN`).
- Never swallow `asyncio.CancelledError` silently; always re-raise or break the loop.

---

## 5. Common Tasks (Recipes)

### 5.1 Add a new enum

1. Open `src/signals_lab/domain/enums.py`.
2. Add the enum (inherit from `str, Enum` or `int, Enum`).
3. Re-export from `src/signals_lab/domain/__init__.py` if it's a top-level public type.
4. Add a unit test in `tests/unit/domain/test_enums.py`.

### 5.2 Add a new domain model

1. Create or edit `src/signals_lab/domain/<topic>.py`.
2. Inherit from `BaseModel`; add `model_config = ConfigDict(arbitrary_types_allowed=True)`.
3. Add `Field(..., description=...)` on every field; validators for invariants (e.g. `ge=0, le=100`).
4. Add `from __future__ import annotations` and `TYPE_CHECKING` import for cross-module refs.
5. **Do not** import anything from `storage/`, `ingestion/`, `api/`, `features/`, `signals/`, `evaluation/`.
6. Add unit tests asserting: (a) construction from valid payload, (b) rejection of invalid payload, (c) all computed properties.

### 5.3 Add a new data provider

1. Add the provider's settings to `config/settings.yaml` under the appropriate `ingestion.<topic>.providers[]` list.
2. Add the API key env var to `.env.example`.
3. Create a new `BaseProvider` subclass in the appropriate `ingestion/<topic>_ingestor.py` (or a new file under `ingestion/providers/`).
4. Register the provider in the ingestor's constructor (read from `get_settings()`).
5. If it's a major provider, add a fixture in `tests/fixtures/` and a `Mock<Name>Provider` for testing.
6. Add an integration test in `tests/integration/ingestion/` (mark with `@pytest.mark.requires_api` if it needs real keys).

### 5.4 Add a new feature

1. Add a new `FeatureDefinition` entry in `feature_registry` (or seed it from YAML).
2. Implement the computation in `features/families/<family>.py` (planned module).
3. The function MUST accept `(observations: List[Observation], params: dict) -> Decimal` and use **only** observations with `time ≤ t`.
4. Register the feature in `FeatureRegistry` (planned) so it gets computed each cycle.
5. Add a unit test asserting: (a) correct value on a known fixture, (b) no-look-ahead (give it future data and confirm it's ignored).

### 5.5 Add a new signal rule

1. Add a new `SignalRule` to the `signal_rules` table (or seed from YAML in Stage 2).
2. The rule references `required_features` and `conditions` (a predicate tree — exact schema TBD; see [SPECS §17](./SPECS.md#17-open-spec-questions--todo)).
3. Add a test asserting: (a) rule fires when conditions met, (b) does not fire when conditions unmet, (c) respects `cooldown_hours`.

### 5.6 Add a new API endpoint

1. Add a Pydantic schema in `api/schemas/<topic>.py` (planned).
2. Add the route handler in `api/routes/<topic>.py` (planned). Use `Depends(get_api_key)` for auth.
3. Map the Pydantic `Signal` / `EvaluationMetrics` schema to the response model.
4. Add an OpenAPI description and example.
5. Add an integration test in `tests/integration/api/` using `httpx.AsyncClient` against the FastAPI app.

### 5.7 Add a config knob

1. Add the field to the appropriate `*Settings` Pydantic class in `src/signals_lab/config.py`.
2. Add a default in the same class.
3. Document it in `config/settings.yaml` with a comment explaining the units, default, and acceptable range.
4. Reference it in code via `get_settings().<path>.<field>` — never via `os.environ.get(...)`.

---

## 6. Testing Conventions

- **Framework:** `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"`).
- **Markers:** use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.requires_api`.
- **Coverage target:** ≥80% on touched lines (`pyproject.toml` `[tool.coverage.report]`).
- **Test files:** `test_<module>.py`, classes `Test<Thing>`, functions `test_<behavior>`.
- **Domain tests:** no I/O, no DB, no HTTP. Just construct Pydantic models and assert.
- **Ingestion tests:** use `Mock*Provider`; never hit the real network in unit tests.
- **Storage tests:** use a real or testcontainer DB; never mock the SQL away.
- **Async tests:** just `async def test_...`; no `@pytest.mark.asyncio` needed (mode is `auto`).

```python
# tests/unit/domain/test_signals.py
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from signals_lab.domain.signals import Signal
from signals_lab.domain.enums import SignalClass, SignalSide, ConfidenceBand, MarketRegime
from signals_lab.domain.market import AssetPair

def test_signal_is_publishable_only_for_high_extreme():
    pair = AssetPair(symbol="BTC/USDT", base="BTC", quote="USDT", exchange="binance")
    sig = Signal(
        asset_pair=pair,
        signal_class=SignalClass.LONG_CANDIDATE,
        side=SignalSide.BUY,
        confidence_score=Decimal("75"),
        confidence_band=ConfidenceBand.HIGH,
        regime=MarketRegime.TRENDING_UP,
        thesis="Momentum + trend alignment, RSI 60, MACD bullish cross.",
        invalidation_condition="4h close below 50EMA",
    )
    assert sig.is_publishable is True
```

---

## 7. Anti-Patterns (DO NOT)

- ❌ **Don't add live trading code.** No `ccxt.create_order`, no `binance.create_oco_order`, no "execute" methods. (See [SPECS §1](./SPECS.md#1-mission--scope).)
- ❌ **Don't import from `storage/` or `ingestion/` inside `domain/`.** Domain stays pure.
- ❌ **Don't use `float` for money or ratios.** Use `Decimal`.
- ❌ **Don't use `time.time()` for timestamps.** Use `datetime.now(timezone.utc)` or `datetime.utcnow()` (for backward compat — prefer the former for new code).
- ❌ **Don't use `print()` in `src/signals_lab/`.** Use `structlog`.
- ❌ **Don't catch bare `except:`** in domain code.
- ❌ **Don't add I/O to `domain/`** even "temporarily". Use the repository interfaces in `storage/`.
- ❌ **Don't bypass the publish gate** (`is_publishable` / `min_confidence_for_publish`). All other bands are internal only.
- ❌ **Don't introduce a new top-level dependency** without a justifying commit message.
- ❌ **Don't write code that mutates shared state without locking** (we use `asyncio`; trust the event loop, but don't share mutable globals).
- ❌ **Don't use `dict` for fixed-shape domain data** when a Pydantic model exists.
- ❌ **Don't use `Optional` when a default is fine** — and vice-versa.

---

## 8. Look-Ahead Bias Checklist (CRITICAL)

Before merging any feature or signal logic, ask:

1. ✅ Does the feature at time `t` use **only** observations with `time ≤ t`?
2. ✅ Are entry prices determined by the **next bar after** `generated_at`, not the current bar?
3. ✅ Are paper-trade exits computed against observations that **actually existed** at exit time? (For backfills, this means simulating the clock.)
4. ✅ Is there any `.shift(-1)`, `.pct_change().shift(-1)`, or `iloc[-1]`-style usage? → **Stop. Refactor.**
5. ✅ Is `signal.expiry_at` always `> signal.generated_at`?
6. ✅ Is `paper_position.entry_time` always `>= signal.generated_at`?

If you answer NO to any of these, the code is broken. Refactor and add a regression test.

---

## 9. Workflow Tips for AI Agents in Cursor

### 9.1 Read order for new tasks

1. **Read this file (AGENTS.md)** — orient yourself on rules and module map.
2. **Read the relevant `ARCHITECTURE.md` section** — understand the high-level design.
3. **Read the relevant `SPECS.md` section** — understand the data contracts and invariants.
4. **Read the existing code in the target module** before adding new code. Match style.
5. **Search for prior art** with `search_files` / `grep` before inventing a new pattern.
6. **Plan with a checklist** using the `task_progress` parameter.
7. **Make small, focused changes** — one logical unit per turn when possible.

### 9.2 Proposing a change

- Open with a 1-sentence summary of what you intend to do.
- Reference the SPECS section(s) the change touches (e.g., "touches SPECS §5.1, §9.1").
- List the files you intend to create/modify.
- Ask clarifying questions if the spec is ambiguous (use `ask_followup_question`).
- Never silently change a public surface (enums, model fields, config keys, API routes). Add a deprecation path or bump the version.

### 9.3 Before claiming "done"

Run the quality gates from [SPECS §13](./SPECS.md#13-quality-gates--tooling):

```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/signals_lab
pytest -m unit --cov=src/signals_lab
```

If any fail, fix them in the same change. Don't leave the user with broken tooling.

### 9.4 Commit message style

Follow conventional commits. Reference SPECS sections.

```
feat(signals): add ConfidenceCalibrator

- Implements settings.signals.confidence_bands mapping
- Touches SPECS §4.2, §9.1
- Adds tests covering all 4 bands (LOW/MEDIUM/HIGH/EXTREME)
- Coverage: 100% on new code
```

---

## 10. Stage 2 Entry Point (current focus)

Stage 2 is **in progress**. The immediate next steps for an AI agent picking up where Stage 1 left off:

1. **Wire up Alembic** in `storage/` for both TimescaleDB and PostgreSQL.
2. **Implement the `FeatureRegistry`** in a new `features/registry.py`.
3. **Implement the `FeatureEngine`** in `features/engine.py` — must enforce the no-look-ahead rule.
4. **Implement Trend, Momentum, Mean-reversion, Volatility families** under `features/families/`.
5. **Stub the Social / Onchain / Events families** with `NotImplementedError` markers (we'll fill in Stage 2.5 when API keys arrive).
6. **Implement `RuleEngine`** in `signals/rules.py` (a starter predicate-tree evaluator).
7. **Implement `ConfidenceCalibrator`** in `signals/confidence.py`.
8. **Add unit tests** for every new component (≥80% coverage).
9. **Update SPECS.md** with any spec changes that emerged during implementation.
10. **Update AGENTS.md** if you added a new pattern, anti-pattern, or module.

---

## 11. Quick Reference: Snippets

### 11.1 Reading the active settings

```python
from signals_lab.config import get_settings
settings = get_settings()
# Reload if you changed config/settings.yaml at runtime:
settings = get_settings(reload=True)
```

### 11.2 Adding a Pydantic model to the domain

```python
# src/signals_lab/domain/market.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class AssetPair(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    symbol: str
    base: str
    quote: str
    exchange: str
    is_active: bool = True
    metadata: dict = Field(default_factory=dict)

    @property
    def normalized_symbol(self) -> str:
        return self.symbol.replace("/", "").upper()
```

### 11.3 Storing a time-series observation

```python
# Anywhere in src/signals_lab/ EXCEPT domain/
from signals_lab.storage.timeseries import TimescaleDBClient
from signals_lab.domain.enums import ObservationType

async def store_market_obs(client: TimescaleDBClient, obs: MarketObservation) -> bool:
    return await client.store_observation(ObservationType.MARKET, obs)
```

### 11.4 Structured log line

```python
import structlog
log = structlog.get_logger(__name__)
log.info("signal_generated", signal_id=str(signal.signal_id), confidence=str(signal.confidence_score))
```

### 11.5 Building a feature deterministically (no I/O)

```python
# src/signals_lab/features/families/trend.py
from decimal import Decimal
from typing import List

def sma(closes: List[Decimal], period: int) -> Decimal:
    if len(closes) < period:
        return Decimal("NaN")  # Or raise; convention is to return NaN for downstream gating.
    window = closes[-period:]  # SAFE: only uses historical closes
    return sum(window) / Decimal(period)
```

---

## 12. Final Words

This codebase is research-grade. Every change should be **defensible**: if someone asks "why did you do it this way?", there should be a SPECS section or a code comment explaining the rationale.

When in doubt, **choose the boring, well-tested option**. Crypto trading is hard; the platform itself should be a paragon of boring, correct engineering.

**Happy hacking. May your signals be high-confidence and your look-aheads be zero.**
