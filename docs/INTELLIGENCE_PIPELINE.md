# Multi-Source Crypto Intelligence Pipeline — Architecture Proposal

> **Status:** Design proposal (Stage 2.5 → Stage 3) · **Last updated:** 2026-06-06  
> **Problem:** Pipeline too dependent on NewsAPI (rate limits) and LunarCrush (402/paid). Health failures block confidence in the whole system.  
> **Goal:** Resilient, explainable, multi-source intelligence with **Tier A always-on**, **Tier B enrich-only**, **Tier C derived scoring**.

**Constraints (unchanged):** Paper research only · No look-ahead · Backend aggregates all external data · UI never calls providers directly · Modular provider swap.

**Companion:** [SPECS.md](../SPECS.md) · [ARCHITECTURE.md](../ARCHITECTURE.md) · [FRONTEND_PRODUCT_PLAN.md](./FRONTEND_PRODUCT_PLAN.md)

---

## Executive summary

| Today | Target |
|---|---|
| Events = mock + NewsAPI config | **Tier A** RSS + cryptocurrency.cv + exchange/protocol feeds always on |
| Social = LunarCrush only | **Reddit** + optional X + Tier B LunarCrush enrich |
| Signals from technical features alone | **Fusion engine**: narrative + social velocity + market confirmation |
| Health = per-provider ping | **Pipeline health**: ingest → normalize → enrich → score → publish + fallback + contribution share |

**Design principle:** No signal class may depend on a single provider. Premium APIs **enrich** scores; their absence **reduces confidence**, never zeroes the pipeline.

---

## 1. Source categories & recommended providers

### 1.1 Provider matrix by category

| Category | **Primary (Tier A)** | **Optional enrich (Tier B)** | Notes |
|---|---|---|---|
| **Crypto-native news** | [cryptocurrency.cv](https://cryptocurrency.cv) JSON/RSS; direct RSS (CoinDesk, Cointelegraph, The Block, Decrypt, Blockworks) | NewsAPI `everything` | cv aggregates 130+ sources; **self-hostable (MIT)** for lock-in escape |
| **Mainstream financial news** | RSS: Reuters `crypto`, FT Alphaville (where ToS allows), Federal Reserve / ECB press RSS | NewsAPI | Macro/regulatory catalysts; low frequency, high credibility when primary |
| **Reddit** | Reddit OAuth API (`r/cryptocurrency`, `r/bitcoin`, `r/ethfinance`, `r/CryptoMarkets`) | — | Free tier: 100 req/min with OAuth; store post id + score + comments |
| **X / Twitter** | Defer MVP; queue via **webhook/manual ingest** or public RSS bridges (fragile) | X API v2 Basic ($100/mo) or Tier B vendor | Do not scrape at scale without legal review; treat as enrich |
| **Telegram** | Bot API: **public channels only** (whitelist: Binance announcements, official protocol channels) | — | No private group scraping |
| **Discord** | Incoming **webhook** on iHabibi-owned server; partner bots later | — | Ingest-only hooks, not Discord client scraping |
| **Exchange blogs** | RSS/HTML: Binance, Coinbase, Kraken, OKX announcement pages | — | High signal for listings, delists, maintenance |
| **Protocol blogs** | RSS: Ethereum, Solana, Arbitrum, Uniswap governance | — | Research-grade development events |
| **Research providers** | RSS: Messari free research, Delphi (if RSS), protocol governance forums (Snapshot API) | Messari Pro, Token Terminal | Governance votes = fundamental events |
| **Market data** | **Binance** (existing): OHLCV, funding, OI via public API/WS | CoinGecko / Coinpaprika for cross-exchange context | Market confirmation layer uses existing feature engine |
| **On-chain / events** | Exchange flow proxies: funding spikes, OI deltas (from market ingest) | Glassnode, CryptoQuant, Dune (export) | On-chain Tier B; start with **market-derived** proxies |
| **Influencer tracking** | First-party registry (YAML/DB) + Reddit/X when available | LunarCrush influencer fields | Historical accuracy scored in Tier C |

### 1.2 Primary vs optional (decision table)

| Role | Providers |
|---|---|
| **Must work with zero paid keys** | cryptocurrency.cv, ≥5 direct RSS feeds, Reddit OAuth, Binance market, exchange announcement RSS |
| **Should work day-one in prod** | Above + CoinGecko metadata (categories, market cap rank) |
| **Nice-to-have enrich** | NewsAPI, LunarCrush, Glassnode, X API |
| **Never blocking** | CryptoPanic, paid social sentiment vendors |

### 1.3 Competitor pattern lens

| Pattern | Source | Adopt? |
|---|---|---|
| Multi-source news aggregation | cryptocurrency.cv, CryptoPanic | ✅ Tier A aggregator + own dedup |
| Smart-money / whale labels | Nansen, Glassnode | ⬜ Tier B; proxy via funding/OI first |
| Social dominance | LunarCrush | ⬜ Enrich only; replace base with Reddit velocity |
| Alert + indicator confirmation | TradingView | ✅ Market confirmation gate |
| Research reports | Messari | ✅ RSS + `research-grade development` class |

---

## 2. Tiered provider system

```
┌─────────────────────────────────────────────────────────────────┐
│ Tier A — Base layer (always on, open/low-friction)              │
│  cryptocurrency.cv · RSS fan-in · Reddit · Binance · CG metadata │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier B — Premium enrichers (optional, non-blocking)             │
│  NewsAPI · LunarCrush · Glassnode · X API                        │
│  → merged as enrichment fields; pipeline continues if DOWN       │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier C — First-party derived intelligence                        │
│  dedup · credibility · narrative cluster · entity extract       │
│  sentiment · novelty · market confirmation · influencer accuracy  │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
                    CanonicalIntelligenceItem
                                ▼
              NarrativeSignalEngine (multi-source fusion)
                                ▼
                    Signal (existing domain) + provenance
```

### Tier A implementation notes

| Source | Auth | Rate limit strategy | Fallback |
|---|---|---|---|
| cryptocurrency.cv | None (hosted); optional key for higher limits | Cache 60s; respect 100/15min hosted | Self-host OR RSS fan-in only |
| Direct RSS | None | 1 req/feed/5min; ETag/If-Modified-Since | Per-feed circuit breaker |
| Reddit | OAuth client credentials | 100/min; batch subreddits | Drop Reddit enrich, not pipeline |
| CoinGecko | Demo key optional | 10–30/min demo | Static asset metadata cache |
| Binance | None for public | Existing 1200/min | Secondary exchange (Bybit) later |

### Tier B degrade behavior

When Tier B is `DOWN` or `DEGRADED`:

- Set `enrichment_status: partial` on affected items
- Apply **confidence penalty** (e.g. −5 to −15 points), not hard stop
- Health UI shows **contribution share lost**, not red entire pipeline
- Signal rules: no rule may require Tier B field as sole trigger

---

## 3. Canonical event model

Introduce **`IntelligenceItem`** — normalized unit for all non-OHLCV intelligence. Existing `EventObservation` and `SocialObservation` become **legacy views** or mappers from `IntelligenceItem`.

### 3.1 Schema (domain)

```python
# src/signals_lab/domain/intelligence.py (proposed)

class SourceType(str, Enum):
    NEWS = "news"
    REDDIT = "reddit"
    X = "x"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    RESEARCH = "research"
    EXCHANGE = "exchange"
    PROTOCOL = "protocol"
    MARKET = "market"
    ONCHAIN = "onchain"
    INFLUENCER = "influencer"

class ContentRole(str, Enum):
    PRIMARY = "primary"       # original report / announcement
    COMMENTARY = "commentary" # analysis of someone else's news
    REPOST = "repost"         # syndicated / copied headline
    RUMOR = "rumor"           # unverified claim

class IntelligenceItem(BaseModel):
    id: UUID                          # internal uuid
    external_id: str                  # provider-native stable id
    dedup_key: str                    # simhash cluster id
    observed_at: datetime             # provider timestamp (UTC)
    ingested_at: datetime

    provider: str                     # e.g. "cryptocurrency_cv", "rss_coindesk"
    provider_tier: Literal["A", "B", "C"]
    source_type: SourceType
    original_source: str              # human name: "CoinDesk", "r/cryptocurrency"
    content_role: ContentRole

    url: Optional[str]
    message_id: Optional[str]         # social message id

    title: str
    body: str
    language: str                     # ISO 639-1
    translated_text: Optional[str]      # en normalized for NLP

    asset_tags: list[str]             # BTC, ETH, SOL
    entity_tags: list[str]            # SEC, Binance, BlackRock

    # Tier C scores (0–1 unless noted)
    sentiment_score: Optional[Decimal]  # -1 to 1
    credibility_score: Decimal
    novelty_score: Decimal
    engagement_score: Optional[Decimal] # normalized 0–1
    social_velocity: Optional[Decimal]  # mentions/hour delta

    cross_source_confirmation_count: int
    confirming_providers: list[str]
    narrative_cluster_id: Optional[str]

    market_reaction: Optional[MarketReactionWindow]
    signal_contribution: Optional[SignalContribution]

    raw_payload_ref: Optional[str]    # S3/DB pointer, not full blob in signal path
    enrichment: dict[str, Any]        # Tier B fields (lunarcrush, newsapi extras)

class MarketReactionWindow(BaseModel):
    asset: str
    window_start: datetime
    window_end: datetime
    return_pct: Decimal
    volume_zscore: Optional[Decimal]
    funding_delta: Optional[Decimal]
    oi_delta_pct: Optional[Decimal]
    confirmed: bool                   # passed market confirmation gate

class SignalContribution(BaseModel):
    narrative_class: str
    weight: Decimal
    confidence_delta: Decimal
    explain_snippet: str
```

### 3.2 JSON example (API / UI)

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "external_id": "cv:abc123",
  "dedup_key": "simhash:9f3a2b1c",
  "observed_at": "2026-06-06T18:00:00Z",
  "provider": "cryptocurrency_cv",
  "provider_tier": "A",
  "source_type": "news",
  "original_source": "The Block",
  "content_role": "primary",
  "url": "https://…",
  "title": "Spot ETH ETF sees record inflows",
  "asset_tags": ["ETH", "BTC"],
  "entity_tags": ["BlackRock", "SEC"],
  "language": "en",
  "sentiment_score": "0.42",
  "credibility_score": "0.85",
  "novelty_score": "0.71",
  "engagement_score": null,
  "social_velocity": "2.3",
  "cross_source_confirmation_count": 4,
  "confirming_providers": ["cryptocurrency_cv", "rss_coindesk", "rss_cointelegraph", "reddit"],
  "narrative_cluster_id": "etf-inflows-2026-06",
  "market_reaction": {
    "asset": "ETH",
    "return_pct": "0.018",
    "volume_zscore": "1.6",
    "confirmed": true
  },
  "signal_contribution": {
    "narrative_class": "market_confirmed_breakout_catalyst",
    "weight": "0.22",
    "confidence_delta": "8",
    "explain_snippet": "ETF inflows confirmed by 4 sources + 1.8% ETH move on volume"
  },
  "enrichment": {
    "lunarcrush_galaxy_score": null,
    "newsapi_available": false
  }
}
```

### 3.3 Storage

| Store | Contents |
|---|---|
| **TimescaleDB** `intelligence_items` hypertable | Full item history, indexed by `observed_at`, `asset_tags`, `dedup_key` |
| **PostgreSQL** `narrative_clusters`, `provider_health_snapshots`, `influencer_registry` | Relational metadata |
| **PostgreSQL** `intelligence_dedup_index` | simhash → canonical id |

---

## 4. Signal logic — multi-source fusion

### 4.1 Signal classes (narrative-aware)

| Class | Trigger sketch | Market confirmation |
|---|---|---|
| `narrative_emerging` | Novelty ↑, cluster age < 6h, confirmation ≥ 2 sources | Optional |
| `sentiment_spike` | Social velocity ↑, Reddit score slope | Required soft (volume z ≥ 1) |
| `breaking_fundamental_event` | Exchange/protocol primary source, credibility ≥ 0.8 | Required within 4h window |
| `crowding_overheated_social` | Sentiment extreme + velocity high | **Negative** gate: fade when funding extreme |
| `unconfirmed_rumor` | Single source OR content_role=rumor | Never publish externally |
| `research_grade_development` | Protocol blog / governance / research RSS | Optional |
| `market_confirmed_breakout_catalyst` | News + confirmation ≥ 3 + return + volume | Required hard |

Map to existing `SignalClass` (LONG/SHORT/WATCH) via **`NarrativeSignalEngine`** — narrative class modulates confidence and thesis text, not side alone.

### 4.2 Fusion formula (explainable)

At time `t`, for asset `a`:

```
fusion_score(a, t) =
    w_cred  * credibility(a, t)
  + w_rel   * relevance(a, t)
  + w_nov   * novelty(a, t)
  + w_vel   * social_velocity_norm(a, t)
  + w_conf  * min(1, confirmation_count / 3)
  + w_mkt   * market_confirmation(a, t)
  - w_decay * time_decay_hours(event_age)
  - w_noise * noise_penalty(item)
```

Default weights (tunable in `config/intelligence.yaml`):

| Weight | Default | Source |
|---|---|---|
| `w_cred` | 0.20 | Tier C credibility model |
| `w_rel` | 0.15 | asset tag match + entity relevance |
| `w_nov` | 0.15 | Tier C novelty |
| `w_vel` | 0.15 | Reddit/X engagement derivatives |
| `w_conf` | 0.20 | cross-source confirmation |
| `w_mkt` | 0.25 | feature engine at t (no look-ahead) |
| `w_decay` | 0.10/h | exponential half-life 8h news, 2h social |
| `w_noise` | 0.10 | repost/clickbait penalties |

**Hard gates (no signal unless passed):**

1. `confirmation_count >= 2` OR (`credibility >= 0.85` AND `content_role == primary`)
2. `unconfirmed_rumor` → internal band only, never publishable
3. `crowding_overheated_social` without negative funding/OI check → downgrade to WATCH
4. **No single-provider rule** — enforced in `RuleEngine` predicate schema

### 4.3 Integration with existing signal engine

```
MarketObservations ──► FeatureEngine ──► technical features
                                              │
IntelligenceItems ──► NarrativeScorer ──► narrative features ──► RuleEngine ──► Signal
                              ▲                                      │
                              └──────── provenance: all item ids ────┘
```

Each `Signal.contributing_factors` gains `source_type: intelligence` entries referencing `IntelligenceItem.id`.

---

## 5. Anti-noise protections (Tier C)

| Protection | Method | Module |
|---|---|---|
| Syndication dedup | Simhash on normalized title + first 500 chars | `intelligence/dedup.py` |
| Clickbait penalty | Title pattern heuristics + low credibility domain list | `intelligence/credibility.py` |
| Copied headlines | Same `dedup_key` within 24h → keep highest credibility only | `dedup.py` |
| Spam social | Account age, karma floor, rate limits | `ingestion/providers/social/reddit.py` |
| Influencer accuracy | Rolling hit rate vs subsequent 4h market move | `intelligence/influencer_accuracy.py` |
| Primary vs commentary | RSS `<category>`, URL path heuristics, LLM optional later | `intelligence/content_role.py` |
| Social without market | If `w_mkt * market_confirmation < threshold` → suppress publish | `intelligence/market_confirmation.py` |

**Credibility score inputs:** source allowlist tier, domain age, historical false-positive rate, `content_role`, cross-confirmation boost.

---

## 6. Health & observability

### 6.1 Provider health model (extend)

```python
class ProviderHealthSnapshot(BaseModel):
    provider: str
    tier: Literal["A", "B", "C"]
    status: Literal["UP", "DEGRADED", "DOWN", "CIRCUIT_OPEN"]
    lag_seconds: int | None
    last_success_at: datetime | None
    last_error: str | None
    quota_used_pct: Decimal | None      # NewsAPI, Reddit
    quota_resets_at: datetime | None
    fallback_active: str | None           # e.g. "rss_fan_in" when cv down
    items_ingested_24h: int
    contribution_share_24h: Decimal       # % of fusion weight supplied
    confidence_impact_if_down: Decimal    # estimated max confidence loss
```

### 6.2 Pipeline stage health

| Stage | OK | DEGRADED | DOWN |
|---|---|---|---|
| **ingest** | all Tier A < 5m lag | any Tier A 5–15m | any Tier A > 15m or all news down |
| **normalize** | < 1m queue depth | 1–5m backlog | worker dead |
| **enrich** | Tier B optional | Tier B all down (warn) | N/A — not blocking |
| **score** | last run < 10m | 10–20m | > 20m |
| **publish** | last signal < 10m | 10–15m | > 15m |

### 6.3 UI improvements ([FRONTEND_PRODUCT_PLAN](./FRONTEND_PRODUCT_PLAN.md))

| Component | Shows |
|---|---|
| `ProviderHealthCard` | tier badge, quota bar, fallback label, contribution % |
| `PipelineStageStrip` | ingest → normalize → enrich → score → publish |
| `ConfidenceImpactBanner` | "LunarCrush down: social velocity −12% weight; confidence cap −8" |
| Signal detail `SourceAttributionPanel` | list of `IntelligenceItem` with credibility, role, links |
| `NarrativeClassBadge` | e.g. `market_confirmed_breakout_catalyst` |

---

## 7. Backend module plan

### 7.1 New / changed modules

```
src/signals_lab/
├── domain/
│   ├── intelligence.py          # NEW: IntelligenceItem, enums, MarketReactionWindow
│   └── signals.py               # EXTEND: ContributingFactor.source_item_id
├── ingestion/
│   ├── base.py                  # EXTEND: ProviderTier, circuit breaker, quota tracking
│   ├── providers/               # NEW: one file per provider family
│   │   ├── news/
│   │   │   ├── cryptocurrency_cv.py
│   │   │   ├── rss_feed.py      # generic RSS with feed registry YAML
│   │   │   └── newsapi.py       # Tier B, moved from mock
│   │   ├── social/
│   │   │   ├── reddit.py
│   │   │   └── lunarcrush.py    # Tier B enrich only
│   │   ├── market_context/
│   │   │   └── coingecko.py
│   │   └── announcements/
│   │       └── exchange_rss.py
│   ├── intelligence_ingestor.py # NEW: fan-in all intelligence providers
│   └── normalizer.py            # NEW: raw → IntelligenceItem
├── intelligence/                # NEW package (I/O via storage, not domain imports)
│   ├── engine.py                # orchestrate dedup → score → cluster
│   ├── dedup.py
│   ├── credibility.py
│   ├── novelty.py
│   ├── sentiment.py             # lexicon first; optional VADER
│   ├── clustering.py            # embedding cluster (Stage 4)
│   ├── market_confirmation.py   # uses FeatureEngine outputs at t
│   └── influencer_registry.py
├── signals/
│   ├── narrative_engine.py      # NEW: fusion → narrative features
│   └── rules.py                 # EXTEND: multi-source predicates
├── storage/
│   └── intelligence_repository.py # NEW
└── workers/
    └── intelligence_worker.py   # NEW cron: ingest + normalize + score

config/
├── intelligence.yaml            # NEW: feeds, weights, allowlists, tiers
└── settings.yaml                # wire ingestion.intelligence section
```

### 7.2 Config: `config/intelligence.yaml` (sketch)

```yaml
tiers:
  A: [cryptocurrency_cv, rss, reddit, binance_market, coingecko_meta, exchange_rss]
  B: [newsapi, lunarcrush, glassnode]

rss_feeds:
  - id: coindesk
    url: https://www.coindesk.com/arc/outboundfeeds/rss/
    credibility: 0.85
  - id: cointelegraph
    url: https://cointelegraph.com/rss
    credibility: 0.75
  # …

reddit:
  subreddits: [cryptocurrency, bitcoin, ethfinance, CryptoMarkets]
  min_karma: 50

fusion_weights:
  credibility: 0.20
  relevance: 0.15
  novelty: 0.15
  social_velocity: 0.15
  confirmation: 0.20
  market_confirmation: 0.25

fallbacks:
  cryptocurrency_cv:
    on_down: rss_fan_in
  newsapi:
    on_down: skip_enrich
  lunarcrush:
    on_down: reddit_velocity_only
```

### 7.3 Provider abstraction rules

1. Every provider implements `BaseIntelligenceProvider.fetch_raw() → list[RawIntelligenceRecord]`
2. **Only** `normalizer.py` emits `IntelligenceItem`
3. Providers never write signals; never called from frontend
4. Circuit breaker after N failures → `CIRCUIT_OPEN` → fallback id from config
5. All fetches logged with `provider`, `latency_ms`, `item_count`, `quota_remaining`

---

## 8. Implementation roadmap

### Phase A — Tier A news base [MVP] `Stage 2.5`

- [ ] `domain/intelligence.py`
- [ ] `providers/news/cryptocurrency_cv.py` + `rss_feed.py`
- [ ] `config/intelligence.yaml` with 8–10 RSS feeds
- [ ] `intelligence/dedup.py` + `credibility.py` (rules-based)
- [ ] `intelligence_ingestor` + storage hypertable
- [ ] Health: tier badges, fallback, contribution counts
- [ ] **Disable NewsAPI as required** in event ingestor; mock → real Tier A only

### Phase B — Social base [Stage 3]

- [ ] Reddit OAuth provider
- [ ] `social_velocity` + `engagement_score`
- [ ] Cross-source confirmation linker (time window ±30m)
- [ ] `NarrativeSignalEngine` stub → one fusion rule end-to-end test

### Phase C — Market confirmation [Stage 3]

- [ ] `market_confirmation.py` wired to FeatureEngine (volume z, funding, OI)
- [ ] Signal classes: `market_confirmed_breakout_catalyst`, `unconfirmed_rumor`
- [ ] UI: `SourceAttributionPanel`, pipeline stage strip

### Phase D — Tier B enrich + optional [Stage 3–4]

- [ ] NewsAPI / LunarCrush as enrich-only adapters
- [ ] Influencer registry + accuracy tracking
- [ ] Narrative clustering (embeddings) — optional GPU/worker

### Phase E — Self-host & resilience [Stage 4]

- [ ] Self-host cryptocurrency.cv OR full RSS-only mode
- [ ] Telegram public channel bot
- [ ] Discord webhook ingest
- [ ] X API or approved alternative

---

## 9. Tradeoffs & risks

| Choice | Pros | Cons | Verdict |
|---|---|---|---|
| cryptocurrency.cv hosted | Zero setup, 130+ sources | Third-party dependency; fair-use limits | **Primary Tier A** + plan self-host |
| RSS-only | Maximum control, no API keys | Maintenance per feed; no unified search | **Required fallback** |
| Reddit vs LunarCrush | Free, raw engagement | Noisier; needs spam filters | **Replace LunarCrush base** |
| X scraping | Cheap | ToS/legal risk; brittle | **Avoid**; API or manual |
| LLM sentiment | Better nuance | Cost, latency, non-determinism | **Stage 4**; lexicon first |
| Self-host cv (MIT) | Lock-in escape | Ops burden | **Production target** when scaled |

| Risk | Mitigation |
|---|---|
| Aggregator outage | RSS fan-in fallback; cached last 24h items |
| Reddit API policy change | Abstract provider; store raw archive |
| False positives on social spikes | Market confirmation gate |
| Look-ahead in market reaction | Reaction window starts at `observed_at`; features at `t` only |
| Syndicated flood | Simhash dedup + repost penalty |

---

## 10. SPECS sections to add

- **§18** Intelligence pipeline & `IntelligenceItem` schema
- **§19** Provider tier registry & fallback policy
- **§20** Narrative signal classes & fusion weights
- **§21** Health model extensions (quota, contribution, pipeline stages)

---

## 11. Acceptance criteria

- [ ] Pipeline produces `IntelligenceItem`s with **zero Tier B keys** configured
- [ ] NewsAPI down → health WARN, signals still generated with reduced confidence
- [ ] LunarCrush down → Reddit velocity substitutes; no 402 blocking ingest
- [ ] Every publishable signal cites ≥2 intelligence sources OR 1 primary credibility ≥ 0.85 + market confirmation
- [ ] Health page shows tier, fallback, contribution %, confidence impact
- [ ] Signal detail lists source attribution with `content_role` and credibility
- [ ] No frontend provider calls (grep CI check)

---

## 12. Immediate config change (interim)

Until Phase A ships, update operator expectations:

```yaml
# config/settings.yaml — recommended interim flags
ingestion:
  events:
    providers:
      - name: "newsapi"
        enabled: false          # Tier B enrich when implemented
      - name: "cryptocurrency_cv"  # add in Phase A
        enabled: true
  social:
    providers:
      - name: "lunarcrush"
        enabled: false          # until paid OR replace with Reddit
```

---

*Next implementation step: `domain/intelligence.py` + `cryptocurrency_cv` provider + RSS registry — see Phase A checklist.*
