# signals-lab Frontend & Platform UX — Implementation Plan

> **Status:** Draft for implementation · **Audience:** Product, frontend, backend, operators  
> **Companion:** `SPECS.md` §11 (API), `ARCHITECTURE.md`, `apps/web/README.md`

---

## Stack decision

### Comparison

| Criterion | Vite SPA (React) | Next.js App Router | Remix | Astro (islands) |
|---|---|---|---|---|
| Dashboard complexity | Excellent — client-heavy tables/charts | Excellent | Excellent | Poor for dense dashboards |
| SEO / Academy content | Needs prerender or split app | Best-in-class SSR/SSG | Good SSR | Best for docs-only |
| Auth | Supabase client + route guards | Supabase + middleware | Loaders + sessions | Limited |
| Real-time polling (5m signals) | Native TanStack Query | Same | Same | Awkward |
| Deploy on Vercel | Static + edge rewrites | Native | Supported | Native |
| Backend coupling | Clean — FastAPI on Fly is separate | Temptation to add BFF in Next | Same | Split |
| Bundle / perf | Smallest for app shell | Larger runtime | Medium | Smallest marketing |
| Operational simplicity | One SPA artifact | SSR cold starts, more moving parts | Medium | Two-site pattern |

### Recommendation: **Vite + React SPA** (primary)

**Why:** signals-lab is a **research dashboard + developer portal**, not a content SEO product first. The compute/API brain lives on **Fly.io (FastAPI + workers)**; the UI is a **thin, fast client** that polls and visualizes. Vite gives the smallest operational surface, best chart/table performance, and clean separation from the Python domain.

**TanStack Router** over React Router: type-safe routes, nested layouts, loader integration with TanStack Query, file-based codegen.

**When to switch to Next.js (or add a second app):**
- Academy SEO becomes a **top-3 acquisition channel** (100+ indexed lesson pages)
- You need **edge middleware** for geo/compliance on the same origin as marketing
- You want **one repo deploy** that serves both SSR marketing and dashboard with shared auth cookies without CORS
- iHabibi brand site merges with signals-lab marketing at scale

Until then: **Vite SPA on Vercel** + optional **Astro/Next marketing subsite** later is simpler than premature Next adoption.

### Competitor pattern lens

| Pattern | Source | Fit for signals-lab | Feeder vs bot |
|---|---|---|---|
| Alert cards + indicator context | TradingView | Signal feed + explainability | Feeder — no execution |
| Bot marketplace / copy trading | 3Commas | Avoid — implies execution | Bot — out of scope |
| Wallet/smart-money labels | Nansen | On-chain factor display | Feeder |
| Research reports + metrics | Messari, Glassnode, CryptoQuant | Performance + regime panels | Feeder |
| Indicator API as product | TAAPI | API keys + usage metering | Feeder |

---

## 1) Product personas

| Persona | Core jobs | Top screens | Permissions | Success metrics |
|---|---|---|---|---|
| **Researcher** | Tune rules, inspect all bands, run backtests, compare strategies | Signal explorer (all bands), backtest lab, strategy lab, internal performance | `read:signals:internal`, `run:backtest`, `write:rules` (future) | Walk-forward lift, false-positive rate, time-to-insight |
| **iHabibi dashboard consumer** | See publishable signals, understand thesis, track freshness | Signal feed (HIGH/EXTREME), signal detail, performance summary | `read:signals:published`, `read:performance` | Signal clarity score, stale-signal complaints ↓ |
| **Admin / operator** | Monitor ingest, replay failures, manage keys, incidents | Health dashboard, aggregators, admin console, incident log | `admin:*`, `read:health`, `write:config` | MTTR, ingest lag p95 < 60s, publish pipeline uptime |
| **API consumer / subscriber** | Integrate signals, manage keys, track quota | API docs, keys, usage analytics, webhook settings | `read:signals`, scoped API keys | API error rate, latency p95, quota headroom |
| **Beginner / education visitor** | Learn crypto, signals, risk without jargon overload | Academy, glossary overlays, guided signal detail | Public read on academy; optional free tier feed (delayed) | Lesson completion, glossary usage, bounce rate on jargon |

---

## 2) Information architecture

### Route map

```
/                           PUBLIC     Marketing homepage
/academy                    PUBLIC     Education hub
/academy/:slug              PUBLIC     Lesson page
/status                     PUBLIC     Public system status (subset)
/pricing                    PUBLIC     Plans overview
/login                      PUBLIC     Supabase auth
/signup                     PUBLIC     Supabase auth

/app                        AUTH       Dashboard shell
/app/signals                AUTH       Signal explorer (role-filtered)
/app/signals/:id            AUTH       Signal detail
/app/backtests              AUTH       Backtesting lab
/app/backtests/:runId       AUTH       Backtest results
/app/strategies             AUTH       Strategy testing lab
/app/strategies/:runId      AUTH       Strategy run results
/app/health                 AUTH       Full health & aggregators
/app/performance            AUTH       Paper eval metrics
/app/settings               AUTH       Profile, preferences, beginner mode
/app/settings/api-keys      AUTH       Subscriber key management (scoped)

/admin                      ADMIN      Operator console
/admin/providers            ADMIN      Provider config & lag
/admin/ingestion            ADMIN      Failed jobs, replay queue
/admin/incidents            ADMIN      Incident timeline
/admin/users                ADMIN      RBAC management
/admin/audit                ADMIN      Audit log viewer
/admin/feature-flags        ADMIN      Toggle experiments

/docs                       PUBLIC*    API reference (Redoc/Swagger embed or static)
/docs/quickstart            PUBLIC*    Onboarding
/docs/webhooks              AUTH       Webhook setup
/docs/changelog             PUBLIC     Schema versions

* /docs authenticated sections for subscriber-only examples
```

### Access matrix

| Area | Public | Authenticated | Admin |
|---|---|---|---|
| Marketing, Academy | ✅ | ✅ | ✅ |
| Signal feed | Delayed demo only | ✅ (filtered by role) | ✅ all bands |
| Backtest / Strategy lab | ❌ | ✅ researcher+ | ✅ |
| Full health | ❌ | ✅ | ✅ |
| API keys & usage | ❌ | ✅ subscriber | ✅ |
| Admin console | ❌ | ❌ | ✅ |

---

## 3) UX blueprint (major modules)

### Signal feed
- **Purpose:** Scan latest candidates; default view shows publishable only for consumers.
- **Actions:** Filter (asset, band, regime, class), sort (freshness, confidence), open detail, toggle beginner labels.
- **Components:** `SignalCard`, `ConfidenceBadge`, `FreshnessIndicator`, filter bar, virtualized list.
- **States:** Empty ("No HIGH signals — pipeline healthy"), loading skeleton, error with retry + link to `/status`.
- **Mobile:** Card stack; swipe for detail; sticky filter sheet.
- **Beginner mode:** Plain-language band labels; hide z-scores until expanded.

### Signal detail (see §4)
### Backtest builder — see §5
### Strategy testing — see §5
### API health dashboard — see §6
### Aggregator monitor — provider cards with lag sparklines
### API usage analytics — requests/day, error rate, quota bar
### Glossary — `GlossaryTooltip` on every jargon term; `/academy` deep links

**Beginner without annoying power users:** Global **Beginner mode** toggle (settings + per-page?). Default OFF for researchers. When ON: inline plain labels + collapsible "Technical detail" accordions. Power users never see expanded beginner copy unless they opt in.

---

## 4) Signal detail spec — HIGH LONG_CANDIDATE

### Page layout (ASCII)

```
┌─────────────────────────────────────────────────────────────┐
│ BTC/USDT · LONG CANDIDATE · HIGH (78)        [Published ✓] │
│ Generated 4m ago · Expires in 3h 56m · Regime: TRENDING_UP  │
├──────────────────────────┬──────────────────────────────────┤
│ CONFIDENCE               │ FRESHNESS & PIPELINE             │
│ [========78========]     │ Market data: 42s ago ✓           │
│ Band: HIGH (70–84)       │ Features: 4m ago ✓               │
│                          │ Signal engine: 4m ago ✓          │
├──────────────────────────┴──────────────────────────────────┤
│ THESIS (why this appeared)                                  │
│ Momentum + trend alignment: 4h close above 50 EMA, RSI 62,  │
│ MACD bullish cross on 1h.                                   │
├─────────────────────────────────────────────────────────────┤
│ CONFLUENCE FACTORS          │ TIMEFRAME ALIGNMENT           │
│ • trend.sma_50 (bull, 0.25) │ 1h  ███ bullish               │
│ • momentum.rsi_14 (bull)    │ 4h  ██  bullish               │
│ • momentum.macd (bull)      │ 1d  █   neutral               │
├─────────────────────────────┴───────────────────────────────┤
│ INVALIDATION · Stop · Target · Horizon                      │
│ Invalidate: 4h close below 50 EMA                           │
│ Suggested stop: ATR trailing · Take profit: +4.2%           │
├─────────────────────────────────────────────────────────────┤
│ PROVENANCE · rule v1.2.0 · features v1.0.0 · Binance, 14 feat│
├─────────────────────────────────────────────────────────────┤
│ WHAT CHANGED (vs previous signal for asset)                  │
│ Confidence 72→78 · RSI crossed 60 · New 4h bar confirmed    │
├─────────────────────────────────────────────────────────────┤
│ [Beginner view ON]  "This is a research idea, not advice..." │
└─────────────────────────────────────────────────────────────┘
```

### Below publish gate variant
Show banner: **Not published externally** — band MEDIUM (62). Researcher/admin see full detail; consumers redirected unless `read:signals:internal`.

### Sample JSON (feeder-safe detail)

```json
{
  "schema_version": "1.0.0",
  "signal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "dedup_key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "asset_pair": {
    "symbol": "BTC/USDT",
    "base": "BTC",
    "quote": "USDT",
    "exchange": "binance"
  },
  "signal_class": "LONG_CANDIDATE",
  "side": "BUY",
  "confidence_score": "78",
  "confidence_band": "HIGH",
  "is_publishable": true,
  "generated_at": "2026-06-06T18:05:00Z",
  "expiry_at": "2026-06-06T22:05:00Z",
  "regime": "TRENDING_UP",
  "thesis": "Momentum + trend alignment: 4h close above 50 EMA, RSI 62, MACD bullish cross on 1h.",
  "invalidation_condition": "4h close below 50 EMA",
  "expected_holding_horizon": "4h",
  "entry_price": "67250.00",
  "target_price": "70100.00",
  "suggested_stop": {
    "type": "atr_trailing",
    "value": "1.8",
    "reference_price": "67250.00"
  },
  "suggested_sell": {
    "type": "take_profit_pct",
    "value": "4.2",
    "reference_price": "67250.00"
  },
  "contributing_factors": [
    {
      "feature_family": "trend",
      "feature_name": "sma_50_distance",
      "value": "0.012",
      "weight": "0.25",
      "direction": "bullish",
      "description": "Price 1.2% above 50-period SMA on 4h",
      "z_score": "1.4"
    },
    {
      "feature_family": "momentum",
      "feature_name": "rsi_14",
      "value": "62",
      "weight": "0.20",
      "direction": "bullish",
      "description": "RSI in bullish zone without overbought extreme"
    }
  ],
  "timeframe_alignment": {
    "1h": "bullish",
    "4h": "bullish",
    "1d": "neutral"
  },
  "freshness": {
    "market_data_age_seconds": 42,
    "feature_computed_age_seconds": 240,
    "signal_age_seconds": 240
  },
  "provenance": {
    "data_sources": ["binance"],
    "observation_window": "24h",
    "computation_version": "1.0.0",
    "rule_version": "v1.2.0",
    "generated_by": "signal-engine",
    "input_feature_count": 14,
    "computation_time_ms": 87
  },
  "changes_since_previous": {
    "previous_signal_id": "990e8400-e29b-41d4-a716-446655440000",
    "confidence_delta": "6",
    "summary": "RSI crossed 60; new 4h bar confirmed trend"
  },
  "beginner_summary": {
    "headline": "Research suggests upward bias for BTC over the next few hours.",
    "risk_note": "Paper research only. Not financial advice. Signal can fail if price closes below support.",
    "confidence_plain": "Fairly strong agreement across indicators, but not guaranteed."
  },
  "status": "ACTIVE"
}
```

---

## 5) Backtesting & strategy lab

### Backtesting (replay historical signals)
- Select date range, assets, signal classes, confidence bands (including internal bands).
- **Assumptions panel (required):** entry = next bar open after `generated_at`, fees 0.1%, slippage 5 bps, no look-ahead enforced server-side.
- Output: equity curve, hit rate, avg return, max drawdown, decay chart, export CSV/JSON.
- Caveats banner: "Past paper results ≠ future performance; survivorship on listed assets only."

### Strategy testing (user-defined rules)
- Rule builder UI maps to predicate tree (same schema as backend `SignalRule`).
- Parameter versioning: every run stores `rule_snapshot_id`.
- Compare runs side-by-side (diff params highlighted).
- Researcher UX: full factor weights; beginner UX: "Test a simple idea" wizard (RSI + trend templates).

**Anti-look-ahead guardrails (UI + API):**
- Date picker cannot extend beyond last ingested bar (server validates).
- Warning if feature window exceeds available history.
- "As-of simulation clock" displayed prominently.

---

## 6) Health & reliability UX

### Summary strip (traffic lights with nuance)
| Indicator | Green | Amber | Red |
|---|---|---|---|
| Ingest | all providers < 60s lag | any 60–300s | any > 300s or DOWN |
| Features | last run < 20m | 20–40m | > 40m or failed |
| Signals | last gen < 10m | 10–15m | > 15m |
| API | p95 < 500ms, errors < 1% | degraded | outage |

### Drill-down
- Provider card → latency histogram, last error, link to incident.
- Failed ingestion table → replay button (admin), dead-letter count.
- Publish pipeline → count queued / published / suppressed-by-gate.
- Schema version mismatch → banner with migration doc link.

### Operator actions (admin)
- Pause provider, trigger manual ingest, replay DLQ range, acknowledge incident.

---

## 7) Subscription & consumer setup [Stage 4]

| Tier | Signals | API calls/mo | WebSocket | History |
|---|---|---|---|---|
| **Free** | Delayed 15m, HIGH only | 1k | ❌ | 7d |
| **Pro** | Real-time publishable | 50k | ✅ | 90d |
| **Enterprise** | Real-time + metadata | Custom | ✅ + NATS relay | Full |

- API key management: rotate, scope permissions, IP allowlist (enterprise).
- Usage metering: dashboard + email at 80/100% quota.
- Overage: soft cap → 429 with `Retry-After`; hard cap optional.
- Publish gate visibility: docs explain LOW/MEDIUM never in API responses.

---

## 8) API & feeder design

### Transport comparison

| Transport | Latency | Complexity | Best for |
|---|---|---|---|
| REST poll | 30–60s consumer-side | Lowest | MVP, iHabibi dashboard |
| WebSocket | Sub-second push | Medium | Pro subscribers |
| NATS relay | Sub-second fan-out | Highest | Future algo platform |

### Idempotent delivery
- `signal_id` + `dedup_key` (same as signal_id for v1).
- Cursor: `GET /signals/history?since=<ISO8601>&cursor=<token>`.
- Consumers store last cursor; retries safe.

### Sample JSON — list item

```json
{
  "signal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "symbol": "BTC/USDT",
  "signal_class": "LONG_CANDIDATE",
  "side": "BUY",
  "confidence_band": "HIGH",
  "confidence_score": "78",
  "generated_at": "2026-06-06T18:05:00Z",
  "thesis_short": "Trend + momentum alignment on 4h/1h",
  "is_publishable": true
}
```

### Usage event

```json
{
  "event_type": "api.request",
  "timestamp": "2026-06-06T18:10:00Z",
  "api_key_id": "key_abc",
  "route": "GET /api/v1/signals",
  "status_code": 200,
  "latency_ms": 45,
  "bytes_out": 2048
}
```

### Health event

```json
{
  "event_type": "health.snapshot",
  "timestamp": "2026-06-06T18:10:00Z",
  "overall_status": "degraded",
  "providers": {
    "binance": { "status": "UP", "lag_seconds": 42 },
    "newsapi": { "status": "DEGRADED", "lag_seconds": 180 }
  },
  "pipeline": {
    "last_signal_at": "2026-06-06T18:05:00Z",
    "publish_queue_depth": 0
  }
}
```

---

## 9) Technical architecture (Vercel + Fly + Supabase)

```
┌─────────────┐     HTTPS      ┌──────────────────┐
│ Vercel CDN  │ ◄────────────► │ Vite SPA         │
│ apps/web    │                │ (static)         │
└─────────────┘                └────────┬─────────┘
                                        │ REST / WS
                                        ▼
                               ┌──────────────────┐
                               │ Fly.io           │
                               │ FastAPI + workers│
                               │ TimescaleDB      │
                               └────────┬─────────┘
                                        │
                               ┌────────▼─────────┐
                               │ Supabase         │
                               │ Auth, RBAC meta  │
                               │ Portal billing*  │
                               └──────────────────┘
* billing Stage 4 — Stripe via Supabase or separate
```

| Concern | Choice |
|---|---|
| **Deploy split** | Vercel: frontend. Fly: API + workers + DB. Supabase: auth + user/org metadata. |
| **Auth** | Supabase Auth (email/OAuth) → JWT → FastAPI validates + maps roles |
| **RBAC** | `researcher`, `consumer`, `subscriber`, `admin` in Supabase `app_metadata` + API key scopes |
| **Analytics** | Vercel Analytics (marketing) + PostHog or Plausible (product events) |
| **Caching** | TanStack Query staleTime; CDN for static; API `ETag` on `/signals` |
| **Observability** | Sentry (frontend), Fly metrics + Prometheus, structlog correlation IDs |
| **Feature flags** | Supabase table or LaunchDarkly-lite JSON in config |
| **Audit log** | Append-only in Postgres; admin UI reads via FastAPI |
| **Rate limiting** | Fly edge proxy + Redis/Supabase counters per API key |
| **Education content** | Same app `/academy` with MDX modules [MVP]; split to Astro if SEO scales |

---

## 10) Frontend implementation structure

See `apps/web/README.md` and scaffolded folders:

```
apps/web/src/
├── routes/           # TanStack Router file routes
├── features/         # Domain UI modules (signals, health, backtests, auth)
├── components/       # Shared UI (ui/, layout/, signals/)
├── domain/           # TypeScript types + zod schemas (mirror backend)
├── lib/              # api client, supabase, utils, query-client
├── content/          # academy MDX, glossary JSON
└── hooks/            # useAuth, useBeginnerMode, useGlossary
```

| Concern | Choice |
|---|---|
| State / server | TanStack Query (server state), React context (UI prefs) |
| Tables | TanStack Table |
| Charts | Recharts (MVP); lightweight-charts if candlesticks needed |
| Forms | react-hook-form + zod |
| Design system | Tailwind v4 + shadcn/ui primitives |
| Testing | Vitest + Testing Library |
| Monitoring | Sentry browser SDK hook in `main.tsx` |

---

## 11) Component inventory (MVP priority)

| Priority | Component | Key props | States | A11y |
|---|---|---|---|---|
| P0 | `ConfidenceBadge` | `band`, `score`, `size` | default, muted | `aria-label` band+score |
| P0 | `SignalCard` | `signal`, `compact`, `showBeginner` | loading skeleton | heading hierarchy |
| P0 | `FreshnessIndicator` | `ageSeconds`, `thresholds` | fresh, stale, unknown | text + icon not color-only |
| P0 | `HealthChip` | `status`, `label` | up, degraded, down | role=status |
| P0 | `EmptyState` | `title`, `description`, `action` | — | focusable action |
| P1 | `SignalExplainabilityPanel` | `factors`, `timeframes` | expanded/collapsed | accordion keyboard |
| P1 | `GlossaryTooltip` | `termId` | loading term | aria-describedby |
| P1 | `MetricCard` | `label`, `value`, `delta`, `trend` | loading, error | live region for updates |
| P1 | `StatusTimeline` | `events` | empty | list semantics |
| P2 | `BacktestResultsTable` | `rows`, `sort` | empty run | sortable headers |
| P2 | `UsageChart` | `series`, `quota` | no data | chart aria summary |
| P2 | `ApiKeyTable` | `keys`, `onRotate` | empty | confirm on rotate |
| P2 | `AdminActionBar` | `actions`, `incidentId` | disabled | confirm dialogs |

---

## 12) Data model suggestions (TypeScript)

See `apps/web/src/domain/schemas/` for zod definitions mirroring:

- `Signal`, `SignalExplanation`, `SignalVersion`
- `BacktestRun`, `StrategyTestRun`
- `AggregatorStatus`, `ProviderHealth`
- `ApiKey`, `UsageSummary`, `SubscriptionPlan`
- `Incident`, `GlossaryTerm`

---

## 13) Cursor handoff

### A. Phased roadmap

| Phase | Tag | Deliverables |
|---|---|---|
| Scaffold + design tokens + routes | [MVP] | `apps/web`, layout, auth shell, mock data |
| Signal feed + detail + glossary | [MVP] | Core product value |
| Health dashboard (read-only) | [MVP] | Operator visibility |
| FastAPI integration | [Stage 3] | Live data, API keys |
| Backtest lab UI | [Stage 3] | Replay API |
| Strategy lab UI | [Stage 3] | Rule builder |
| Performance dashboards | [Stage 3] | Paper eval metrics |
| Subscription + metering | [Stage 4] | Stripe, quotas |
| WebSocket push | [Stage 4] | Real-time feed |
| NATS relay docs + adapter | [Future algo feeder] | Sub-second consumers |

### B. Build first (Cursor)
1. `domain/schemas/signal.ts` + mock fixtures
2. `lib/api/client.ts` + TanStack Query hooks
3. `SignalCard`, `ConfidenceBadge`, `FreshnessIndicator`
4. `/app/signals` + `/app/signals/$id` routes
5. `/app/health` with provider cards
6. Supabase auth guard on `_authenticated` layout
7. Glossary JSON + `GlossaryTooltip`

### C. SPECS sections to add
- **§11.1** Frontend architecture & deployment
- **§11.2** WebSocket / feeder envelope schema
- **§15** Backtest & strategy simulation API
- **§16** RBAC & Supabase auth mapping
- **§17** Academy content model

### D. MVP acceptance criteria
- [ ] Researcher sees all bands; consumer sees HIGH/EXTREME only
- [ ] Signal detail shows thesis, factors, invalidation, provenance, freshness
- [ ] Beginner mode toggles plain-language layer
- [ ] Health page reflects `signals-lab health apis` data via API
- [ ] Lighthouse performance > 90 on dashboard shell
- [ ] Auth protects `/app/*` and `/admin/*`
- [ ] No live trading UI anywhere

### E. Risks & mitigations

| Risk | Mitigation |
|---|---|
| CORS / auth drift between Supabase and FastAPI | Single JWT validation doc; shared `sub` claim |
| Stale dashboard misleads users | Freshness indicators mandatory on every signal surface |
| Backtest look-ahead | Server-side clock simulation; UI shows as-of time |
| Scope creep into execution | Lint rule: no "buy/order/execute" in frontend routes |
| SEO neglected | Academy as MDX in SPA first; split when traffic warrants |

---

*End of plan — implement against `apps/web` scaffold.*
