# Implementation Prompt — Intelligence News in Dashboard

> **Purpose:** Hand this document to an AI coding agent (or engineer) to add a **live news ticker** and **signal–news attribution** to the signals-lab dashboard.  
> **Status:** Ready for implementation · **Depends on:** Phase A intelligence backend (done), Stage 3 FastAPI (partial/stub OK with mocks first)  
> **Companion docs:** `docs/INTELLIGENCE_PIPELINE.md`, `docs/FRONTEND_PRODUCT_PLAN.md`, `apps/web/README.md`, `AGENTS.md`

---

## Copy-paste agent prompt (start here)

```
Implement the Intelligence News dashboard feature for signals-lab.

Read first:
- docs/prompts/DASHBOARD_INTELLIGENCE_NEWS.md (this file — full spec)
- docs/INTELLIGENCE_PIPELINE.md §3–§4 (IntelligenceItem + fusion)
- apps/web/src/domain/schemas/signal.ts (existing Signal schema)
- src/signals_lab/domain/intelligence.py (backend domain)

Goal: Users see a scrolling news ticker and, on each signal detail page, a clear panel
explaining WHICH news items contributed to WHY that signal appeared.

Constraints (non-negotiable):
- UI never calls external providers (RSS, cryptocurrency.cv, Reddit) directly — only our FastAPI.
- No look-ahead: news items linked to a signal must have observed_at <= signal.generated_at.
- Paper research only — no live trading UI.
- Published signals (HIGH/EXTREME) only for consumer role; internal bands for researchers.
- Match existing apps/web patterns: TanStack Router, TanStack Query, Zod schemas, Tailwind v4.

Deliver in two phases:
Phase 1 (frontend-only, ship first): mock intelligence fixtures + UI components + routes.
Phase 2 (backend wire-up): FastAPI routes + link intelligence items to Signal.contributing_factors.

Acceptance criteria are in §8 of DASHBOARD_INTELLIGENCE_NEWS.md.
```

---

## 1. Product intent

### User story

> As a **researcher or iHabibi consumer**, I want to see **recent crypto intelligence** (news, narratives) in the dashboard and understand **which headlines contributed to a specific signal**, so I can trust the thesis and spot stale or rumor-driven ideas.

### Jobs to be done

| Job | UI surface |
|-----|------------|
| Scan breaking narratives | Global **news ticker** in app shell |
| Filter news by asset | `/app/intelligence` feed + asset chips |
| Understand signal thesis | Signal detail → **“News & narrative context”** panel |
| Trace provenance | Each linked news card shows source, credibility, confirmation count |
| Monitor pipeline | `/app/health` → intelligence provider cards (extend existing) |

### What “because of these news” means (explainability contract)

A signal may cite intelligence in two layers:

1. **Thesis text** — human-readable summary already on `Signal.thesis` (may mention narrative).
2. **Structured attribution** — list of `IntelligenceItem` records (or slim DTOs) with:
   - `title`, `original_source`, `observed_at`, `url`
   - `credibility_score`, `cross_source_confirmation_count`
   - `signal_contribution.explain_snippet` — one line: *why this item mattered*
   - `signal_contribution.weight` / `confidence_delta` — how much it moved confidence

**Rule:** If a news item appears under a signal, the backend must prove temporal validity (`observed_at ≤ generated_at`) and store item IDs in provenance.

---

## 2. Current codebase anchors

### Backend (Phase A — exists)

| Piece | Path |
|-------|------|
| Domain models | `src/signals_lab/domain/intelligence.py` |
| Pipeline | `src/signals_lab/intelligence/engine.py` |
| Ingestor | `src/signals_lab/ingestion/intelligence_ingestor.py` |
| RSS + cv providers | `src/signals_lab/ingestion/providers/news/` |
| Config | `config/intelligence.yaml`, `config/settings.yaml` → `ingestion.intelligence` |
| CLI (no DB) | `signals-lab intelligence fetch` |

### Frontend (scaffold — mock only)

| Piece | Path |
|-------|------|
| Signal list/detail | `apps/web/src/routes/app/signals/` |
| Explainability (technical factors only) | `apps/web/src/components/signals/SignalExplainabilityPanel.tsx` |
| Signal Zod schema | `apps/web/src/domain/schemas/signal.ts` |
| Mock signals | `apps/web/src/domain/fixtures/mock-signals.ts` |
| API client stub | `apps/web/src/lib/api/client.ts` |
| App shell nav | `apps/web/src/components/layout/AppShell.tsx` |

### Not yet built (this prompt)

- `NarrativeSignalEngine` / fusion into `Signal.contributing_factors` (Phase C in `INTELLIGENCE_PIPELINE.md`)
- FastAPI intelligence routes
- Dashboard news ticker + intelligence pages
- `contributing_factors` entries with `feature_family: "intelligence"`

---

## 3. UX specification

### 3.1 Global news ticker (app shell)

Place a **compact horizontal ticker** below the main header on all `/app/*` routes.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ signals-lab          Signals · Intelligence · Health · Settings          │
├──────────────────────────────────────────────────────────────────────────┤
│ ● LIVE  ETH ETF record inflows — The Block (4 sources) · BTC strat… ▶   │
└──────────────────────────────────────────────────────────────────────────┘
```

**Behavior:**

- Auto-scroll / marquee (respect `prefers-reduced-motion` → static list)
- Poll every **60s** via TanStack Query (`staleTime: 30_000`)
- Click headline → `/app/intelligence/$itemId` or external URL (new tab) with `rel="noopener"`
- Badge: `LIVE` when last ingest < 5 min; `DELAYED` otherwise
- Show max **12** headlines in rotation; prioritize:
  1. `cross_source_confirmation_count ≥ 2`
  2. `novelty_score` desc
  3. `observed_at` desc
- Asset pill on items with `asset_tags` (e.g. `ETH`)

**Empty state:** “No recent intelligence — check Health” with link to `/app/health`.

### 3.2 Intelligence feed page — `/app/intelligence`

New route in app nav (between Signals and Health).

**Layout:**

- Filter bar: asset multi-select, source type, min credibility slider, “confirmed only” toggle
- Virtualized list of `IntelligenceCard` components
- Each card: title, source, time ago, credibility bar, confirmation chips, asset tags, excerpt

### 3.3 Intelligence detail — `/app/intelligence/$itemId`

- Full title, body excerpt, metadata row (provider tier, content role)
- “Confirming sources” list when `cross_source_confirmation_count > 1`
- **Related signals** sidebar: signals that cite this item (reverse lookup)
- External link button when `url` present

### 3.4 Signal detail — “News & narrative context” panel

Insert **below Thesis**, **above** existing `SignalExplainabilityPanel`.

```
┌─────────────────────────────────────────────────────────────────┐
│ NEWS & NARRATIVE CONTEXT                          [3 items]     │
├─────────────────────────────────────────────────────────────────┤
│ ▲ Spot ETH ETF sees record inflows                              │
│   The Block · 2h ago · credibility 85% · confirmed ×4         │
│   → +8 confidence: ETF inflows confirmed by 4 sources           │
│   [View story] [View intelligence record]                       │
├─────────────────────────────────────────────────────────────────┤
│ ▲ ETH derivatives reset and the next retail trade               │
│   Blockworks · 5h ago · credibility 85% · confirmed ×1        │
│   → +3 confidence: aligns with momentum regime on ETH           │
└─────────────────────────────────────────────────────────────────┘
│ TECHNICAL CONFLUENCE (existing panel below)                     │
```

**Rules:**

- Sort linked items by `signal_contribution.weight` desc, then `observed_at` desc
- If no linked news: show neutral copy — “No narrative catalyst linked; signal is technical-only.”
- Beginner mode: hide `confidence_delta` numbers; show plain `explain_snippet` only
- Rumor items (`content_role: rumor`): show ⚠ badge; never on publishable-only consumer view unless explicitly internal role

### 3.5 Signal card teaser (optional enhancement)

On `/app/signals` list, if signal has intelligence links, show a small 📰 icon + count:

`📰 2 narratives` — clicking signal detail scrolls to news panel.

### 3.6 Health page extension

Add **Intelligence** section to `/app/health`:

| Provider | Tier | Status | Last fetch | Items (24h) |
|----------|------|--------|------------|-------------|
| rss_fan_in | A | OK | 1m ago | 240 |
| cryptocurrency_cv | A | WARN | 402 / disabled | 0 |

Reuse `HealthChip` pattern from `apps/web/src/components/health/HealthChip.tsx`.

---

## 4. Data contracts

### 4.1 IntelligenceItem DTO (API response)

Mirror backend `IntelligenceItem` with JSON-safe decimals as strings.

```typescript
// apps/web/src/domain/schemas/intelligence.ts

export const intelligenceItemSchema = z.object({
  id: z.string().uuid(),
  external_id: z.string(),
  dedup_key: z.string(),
  observed_at: z.string(),
  ingested_at: z.string(),
  provider: z.string(),
  provider_tier: z.enum(["A", "B", "C"]),
  source_type: z.enum(["news", "social", "announcement", "research", "governance", "unknown"]),
  original_source: z.string(),
  content_role: z.enum(["primary", "secondary", "commentary", "rumor", "official"]),
  url: z.string().url().nullable().optional(),
  title: z.string(),
  body: z.string(),
  language: z.string(),
  asset_tags: z.array(z.string()),
  entity_tags: z.array(z.string()),
  sentiment_score: z.string().nullable().optional(),
  credibility_score: z.string(),
  novelty_score: z.string(),
  cross_source_confirmation_count: z.number().int(),
  confirming_providers: z.array(z.string()),
  narrative_cluster_id: z.string().nullable().optional(),
  signal_contribution: z
    .object({
      narrative_class: z.string(),
      weight: z.string(),
      confidence_delta: z.string(),
      explain_snippet: z.string(),
    })
    .nullable()
    .optional(),
});

export type IntelligenceItem = z.infer<typeof intelligenceItemSchema>;
```

### 4.2 Extend Signal schema — linked intelligence

```typescript
// Add to signalSchema in apps/web/src/domain/schemas/signal.ts

linked_intelligence: z.array(
  z.object({
    intelligence_id: z.string().uuid(),
    item: intelligenceItemSchema, // embedded snapshot at signal time
    contribution_weight: z.string(),
    confidence_delta: z.string(),
    explain_snippet: z.string(),
  }),
).optional(),

narrative_summary: z.string().optional(), // one-line fusion headline for ticker alignment
```

### 4.3 Extend ContributingFactor (backend + frontend)

Add optional fields for intelligence-backed factors:

```python
# src/signals_lab/domain/signals.py — ContributingFactor
source_type: str = "feature"  # "feature" | "intelligence"
intelligence_item_id: Optional[UUID] = None
```

```typescript
// contributingFactorSchema — add optional:
source_type: z.enum(["feature", "intelligence"]).default("feature"),
intelligence_item_id: z.string().uuid().optional(),
```

When `source_type === "intelligence"`, `feature_family` = `"intelligence"`, `feature_name` = narrative_class slug.

### 4.4 API endpoints (FastAPI — Phase 2)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/intelligence/feed` | Paginated feed. Query: `asset`, `limit`, `since`, `min_credibility`, `confirmed_only` |
| `GET` | `/api/v1/intelligence/{id}` | Single item |
| `GET` | `/api/v1/intelligence/ticker` | Top N for marquee (default 12) |
| `GET` | `/api/v1/intelligence/{id}/signals` | Signals citing this item |
| `GET` | `/api/v1/signals/{id}` | Extend existing — include `linked_intelligence` |
| `GET` | `/api/v1/signals/{id}/explanation` | Extend — include `narrative_factors` array |

**Auth:** Same API key as signals. Consumers get items only for publishable signals; researchers get all bands.

**Publish gate:** Ticker may show all ingested news (it's not a trading signal). Signal-linked news on consumer view must come from signals that passed publish gate OR from items attached to publishable signals only.

---

## 5. Component map (frontend)

| Component | Path | Responsibility |
|-----------|------|----------------|
| `NewsTicker` | `apps/web/src/components/intelligence/NewsTicker.tsx` | Marquee, polling, reduced-motion |
| `IntelligenceCard` | `apps/web/src/components/intelligence/IntelligenceCard.tsx` | Feed row |
| `IntelligenceCredibilityBar` | `apps/web/src/components/intelligence/IntelligenceCredibilityBar.tsx` | 0–1 visual |
| `ConfirmationBadge` | `apps/web/src/components/intelligence/ConfirmationBadge.tsx` | “×4 sources” |
| `SignalNewsPanel` | `apps/web/src/components/signals/SignalNewsPanel.tsx` | Signal detail attribution |
| `IntelligenceHealthSection` | `apps/web/src/components/health/IntelligenceHealthSection.tsx` | Provider status |

**Hooks:**

```typescript
// apps/web/src/lib/api/intelligence.ts
useIntelligenceTicker()
useIntelligenceFeed(filters)
useIntelligenceItem(id)
useSignalLinkedIntelligence(signalId) // or embedded in useSignal(id)
```

Use mock fixtures until `VITE_API_BASE_URL` points to real API:

```typescript
// apps/web/src/domain/fixtures/mock-intelligence.ts
export const mockIntelligenceFeed: IntelligenceItem[]
export const mockLinkedIntelligenceBySignalId: Record<string, LinkedIntelligence[]>
```

---

## 6. Backend work (Phase 2)

### 6.1 Storage read paths

Add repository methods in `storage/timeseries.py` (or new `storage/intelligence.py`):

- `fetch_intelligence_feed(since, asset, limit, min_credibility)`
- `fetch_intelligence_by_id(id)`
- `fetch_intelligence_for_signal(signal_id)` — join table or JSONB on signal row

### 6.2 Signal ↔ intelligence link

When `NarrativeSignalEngine` runs (Phase C), persist:

```python
# PostgreSQL — signals_lab relational
signal_intelligence_links (
    signal_id UUID REFERENCES signals(id),
    intelligence_item_id UUID,
    contribution_weight DECIMAL,
    confidence_delta DECIMAL,
    explain_snippet TEXT,
    linked_at TIMESTAMPTZ,
    PRIMARY KEY (signal_id, intelligence_item_id)
)
```

Until Phase C exists, **seed links manually** in fixtures or a dev script that matches mock frontend data.

### 6.3 Provenance

Extend `ProvenanceRecord.data_sources` to include intelligence providers, e.g. `["binance", "rss_fan_in"]`, and add:

```python
intelligence_item_ids: List[UUID] = Field(default_factory=list)
```

---

## 7. Mock data scenario (Phase 1)

Ship UI with one coherent demo story:

**Signal:** BTC/USDT LONG_CANDIDATE HIGH (existing mock `a1b2c3d4-...`)

**Linked news (2 items):**

1. “Strategy playbook looks different in 2026” — Blockworks — BTC tag — weight 0.15 — “Institutional accumulation narrative supports trend”
2. “Yield Basis is making native BTC yield a reality” — Blockworks — BTC tag — weight 0.10 — “Fundamental DeFi narrative adds medium-term bid”

**Ticker:** Include 8–12 items from `signals-lab intelligence fetch` output (copy real titles from RSS) plus the two linked items above marked `signal_contribution` when shown in feed.

**ETH signal** (second mock): link “ETH derivatives reset and the next retail trade” to show multi-asset coverage.

---

## 8. Acceptance criteria

### Phase 1 — Frontend (mock data)

- [ ] `NewsTicker` visible on all `/app/*` pages; respects reduced motion
- [ ] `/app/intelligence` route with filterable feed
- [ ] `/app/intelligence/$itemId` detail page
- [ ] `SignalNewsPanel` on signal detail with linked items, snippets, and empty state
- [ ] Zod schemas + TypeScript types for intelligence DTOs
- [ ] Mock fixtures wired; TanStack Query hooks with `queryFn` swappable via env
- [ ] Nav updated: “Intelligence” link in `AppShell`
- [ ] `npm run build` passes in `apps/web`
- [ ] Basic vitest test for schema parsing mock JSON

### Phase 2 — Backend + wire-up

- [ ] FastAPI routes under `src/signals_lab/api/routes/intelligence.py`
- [ ] `GET /intelligence/ticker` returns ≤12 items, sorted per §3.1
- [ ] Signal detail API returns `linked_intelligence` with temporal validation
- [ ] Health endpoint includes intelligence provider status
- [ ] Unit tests: no look-ahead on link queries (`observed_at <= generated_at`)
- [ ] Integration test: ingest RSS → item in feed → (when Phase C ready) link appears on signal

### Quality gates

```bash
cd apps/web && npm run build && npm run test
ruff check src/ tests/
pytest tests/unit -m unit
```

---

## 9. Visual & accessibility notes

- Ticker must be **keyboard accessible**: pause on focus, items reachable via tab where practical
- Color-code credibility: ≥0.85 strong, 0.6–0.84 neutral, <0.6 muted (not red — avoid alarmism)
- Rumor badge: amber ⚠ with tooltip from glossary term `rumor`
- All timestamps: relative (“2h ago”) + absolute in `title` attribute (UTC)
- Mobile: ticker becomes vertical “Latest” stack; signal news panel single column

---

## 10. Glossary additions

Add to `apps/web/src/content/glossary/terms.ts`:

| Term ID | Label | Plain definition |
|---------|-------|------------------|
| `intelligence` | Intelligence | News and social narratives we ingest, dedupe, and score — not trading advice |
| `credibility` | Credibility | How much we trust a source (0–100%), based on tier, confirmation, and clickbait penalties |
| `confirmation` | Cross-source confirmation | Same story reported by multiple independent providers |
| `narrative-catalyst` | Narrative catalyst | A news item that increased signal confidence via our fusion rules |

---

## 11. Out of scope (do not implement in this task)

- Live trading or “act on news” CTAs
- Direct RSS/API calls from the browser
- Sentiment ML models
- Reddit provider (Phase B)
- Full `NarrativeSignalEngine` unless explicitly scheduled — use mocks/links for Phase 1
- x402 / cryptocurrency.cv payment handling

---

## 12. Suggested implementation order

1. `domain/schemas/intelligence.ts` + mock fixtures  
2. `NewsTicker` + mount in `AppShell`  
3. `/app/intelligence` routes + `IntelligenceCard`  
4. `SignalNewsPanel` + extend mock BTC signal  
5. Extend `SignalExplainabilityPanel` OR keep news separate (preferred: **separate panel**)  
6. Intelligence section on health page (mock provider statuses)  
7. FastAPI routes + repository reads  
8. Phase C fusion engine links real data  

---

## 13. Example API responses

### `GET /api/v1/intelligence/ticker`

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-06-07T00:30:00Z",
  "items": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "title": "Spot ETH ETF sees record inflows",
      "original_source": "The Block",
      "observed_at": "2026-06-06T22:00:00Z",
      "asset_tags": ["ETH"],
      "credibility_score": "0.85",
      "cross_source_confirmation_count": 4,
      "url": "https://example.com/article"
    }
  ]
}
```

### Signal detail excerpt

```json
{
  "signal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "thesis": "Momentum + trend alignment; ETF inflow narrative adds fundamental support.",
  "narrative_summary": "ETF inflows + institutional BTC narrative",
  "linked_intelligence": [
    {
      "intelligence_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "contribution_weight": "0.22",
      "confidence_delta": "8",
      "explain_snippet": "ETF inflows confirmed by 4 sources",
      "item": { "...": "full IntelligenceItem" }
    }
  ],
  "contributing_factors": [
    {
      "feature_family": "intelligence",
      "feature_name": "market_confirmed_breakout_catalyst",
      "source_type": "intelligence",
      "intelligence_item_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "value": "0.85",
      "weight": "0.22",
      "direction": "bullish",
      "description": "ETF inflows confirmed by 4 sources"
    }
  ]
}
```

---

*Last updated: 2026-06-07 · Author: signals-lab platform team*
