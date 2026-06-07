# Deployment Guide — signals-lab

> **Status:** Planning doc for Stage 3+ · **Last updated:** 2026-06-06  
> **Companion:** [FRONTEND_PRODUCT_PLAN.md](./FRONTEND_PRODUCT_PLAN.md) · [SPECS.md §11](../SPECS.md) · [apps/web/README.md](../apps/web/README.md)

---

## TL;DR

| Phase | When | Deploy what |
|---|---|---|
| **1 — Local** | **Now** (Stage 1–2) | Nothing to cloud. Python + Docker Postgres + Vite dev. |
| **2 — API first** | Stage 3: FastAPI serves real signals | **Fly.io** (API + workers + TimescaleDB) |
| **3 — Dashboard** | Fly API stable + CORS configured | **Vercel** (`apps/web` SPA) |
| **4 — Auth & portal** | Need login, API keys, billing | **Supabase** (Auth + portal metadata) |

**Do not deploy all three at once.** The frontend currently uses mock data; cloud infra without a working API adds cost and debugging surface with no user value.

---

## Deploy trigger (definition of “ready”)

Deploy Phase 2 when you can answer **yes** to all of:

- [ ] Alembic migrations apply cleanly against production-shaped DB
- [ ] `signals-lab api serve` returns **real** signals from Postgres (not fixtures)
- [ ] `signals-lab health` passes for APIs + databases in the target environment
- [ ] Publish gate enforced: external routes return HIGH/EXTREME only
- [ ] Paper evaluator writes metrics you can query via API

Deploy Phase 3 (Vercel) when:

- [ ] Fly API URL is stable (e.g. `https://signals-lab-api.fly.dev`)
- [ ] CORS allows your Vercel preview + production origins
- [ ] Frontend `VITE_API_BASE_URL` points at the Fly API (direct or via Vercel rewrite)

Deploy Phase 4 (Supabase) when:

- [ ] You need multi-user login, subscriber API keys, or billing — not for solo researcher dev

---

## Architecture (target production)

```
┌─────────────────┐     HTTPS      ┌──────────────────────┐
│ Vercel          │ ◄────────────► │ apps/web (Vite SPA)    │
│ signals-lab.app │                │ static + /api rewrite  │
└────────┬────────┘                └──────────┬───────────┘
         │ /api/* proxy                         │ Bearer JWT (Stage 4)
         ▼                                      ▼
┌────────────────────────────────────────────────────────────┐
│ Fly.io                                                      │
│  • FastAPI (uvicorn)     port 8000                         │
│  • Workers (ingest / features / signals / eval)             │
│  • TimescaleDB + PostgreSQL (Fly Postgres or attached vol)  │
└────────────────────────────┬───────────────────────────────┘
                             │ auth metadata, orgs (Stage 4)
                             ▼
                    ┌─────────────────┐
                    │ Supabase        │
                    │ Auth + portal   │
                    └─────────────────┘
```

**Division of responsibility**

| Service | Owns | Does NOT own |
|---|---|---|
| **Fly.io** | Python runtime, workers, time-series + relational DB, NATS (optional) | Static frontend, user sign-up UI |
| **Vercel** | Frontend CDN, preview URLs, `/api` rewrite to Fly | Python execution, database |
| **Supabase** | Auth (email/OAuth), user/org metadata, future billing hooks | OHLCV, signals, feature vectors |

---

## Phase 1 — Local development (current)

### Prerequisites

- Python 3.11+ · `./setup.sh`
- Node.js 20+ · `signals-lab web setup`
- Docker (optional) · `signals-lab web docker up`

### Daily commands

```bash
export PATH="$(pwd)/bin:$PATH"

# Backend
./setup.sh
signals-lab web docker up          # TimescaleDB: signals_ts + signals_rel
signals-lab health                 # APIs + DB
signals-lab features compute       # no DB required
# signals-lab api serve            # [Stage 3] FastAPI on :8000

# Frontend
signals-lab web dev                # http://localhost:5173

# After git pull
signals-lab web refresh            # npm deps + env hints
signals-lab web refresh --docker   # also restart Postgres
signals-lab web refresh --force      # stale Vite / HMR issues
```

### Local environment files

| File | Purpose |
|---|---|
| `.env` | Python backend — copy from `.env.example` |
| `apps/web/.env.local` | Vite — copy from `apps/web/.env.example` |
| `config/settings.yaml` | Runtime defaults (override via `SIGNALSLAB_*` env vars) |

### Local env checklist (backend `.env`)

| Variable | Required | Notes |
|---|---|---|
| `SIGNALSLAB_STORAGE__TIMESERIES__URL` | For ingest | Default: `postgresql://postgres:postgres@localhost:5432/signals_ts` |
| `SIGNALSLAB_STORAGE__RELATIONAL__URL` | For signals | Default: `postgresql://postgres:postgres@localhost:5432/signals_rel` |
| `NEWSAPI_KEY` | Optional | Events ingest (mock providers OK for dev) |
| `LUNARCRUSH_API_KEY` | Optional | Social; HTTP 402 = paid tier |
| `IHABIBI_API_KEY` | Stage 3 API | Downstream consumer test key |
| `ADMIN_API_KEY` | Stage 3 API | Internal admin routes |
| `SIGNALSLAB_APP__ENVIRONMENT` | Yes | `development` locally |

### Local env checklist (frontend `apps/web/.env.local`)

| Variable | Local value | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | Vite dev proxy → `localhost:8000` |
| `VITE_API_PROXY_TARGET` | `http://localhost:8000` | Dev only; not used on Vercel |
| `VITE_SUPABASE_URL` | empty | Skip until Phase 4 |
| `VITE_SUPABASE_ANON_KEY` | empty | Skip until Phase 4 |

### CORS for local Vite

Add Vite’s origin to `config/settings.yaml` before testing the real API against the dashboard:

```yaml
api:
  cors_origins:
    - "http://localhost:5173"   # Vite dev server
    - "http://localhost:3000"
```

Or override via env when supported: check `src/signals_lab/config.py` for the exact nested key.

---

## Phase 2 — Fly.io (API + workers + database)

Deploy **first** — the product’s value is the signal pipeline and API, not the static site.

### Recommended Fly resources

| Component | Fly pattern |
|---|---|
| FastAPI | `fly launch` → single app or `signals-lab-api` |
| Workers | Separate Fly Machines / processes, or same app with multiple `cmd` |
| Database | Fly Postgres + Timescale extension, or Timescale Cloud + Fly compute |
| Secrets | `fly secrets set KEY=value` — never commit prod secrets |

### Pre-deploy checklist

- [ ] `fly.toml` created (not in repo yet — add at Stage 3)
- [ ] Production `SIGNALSLAB_APP__ENVIRONMENT=production`
- [ ] `api.reload: false` in prod config
- [ ] Database URLs use Fly internal hostname or TLS connection string
- [ ] All provider API keys set via `fly secrets`
- [ ] Health endpoint exposed: `GET /api/v1/health`
- [ ] Migrations run as release command or one-off `fly ssh console`

### Fly secrets checklist

Set via `fly secrets set` (names match `.env.example`):

```bash
SIGNALSLAB_STORAGE__TIMESERIES__URL=postgresql://...
SIGNALSLAB_STORAGE__RELATIONAL__URL=postgresql://...
NEWSAPI_KEY=...
LUNARCRUSH_API_KEY=...
IHABIBI_API_KEY=...
ADMIN_API_KEY=...
SIGNALSLAB_APP__ENVIRONMENT=production
SIGNALSLAB_APP__LOG_LEVEL=INFO
# NATS_URL=...   # only if events.enabled
```

### Fly deploy sketch (Stage 3)

```bash
# One-time
fly launch --name signals-lab-api --region <closest-to-binance>
fly postgres create   # or attach existing Timescale provider
fly secrets import < .env.production   # sanitized — no comments

# Per release
fly deploy
fly logs
curl https://signals-lab-api.fly.dev/api/v1/health
```

### Acceptance (Phase 2)

- `curl -H "Authorization: Bearer $IHABIBI_API_KEY" https://<fly-app>/api/v1/signals` returns publishable signals
- `signals-lab health` against prod URLs exits 0
- Ingest + feature + signal workers running on schedule (5 min signals, 60s ingest target)

---

## Phase 3 — Vercel (frontend)

Deploy **after** Fly API is stable.

### Project settings

| Setting | Value |
|---|---|
| **Root directory** | `apps/web` |
| **Framework** | Vite |
| **Build command** | `npm run build` |
| **Output directory** | `dist` |
| **Node version** | 20.x |

### Vercel environment variables

| Variable | Production | Preview |
|---|---|---|
| `VITE_API_BASE_URL` | `https://signals-lab-api.fly.dev/api/v1` **or** `/api/v1` if using rewrite | Same pattern with staging Fly URL |
| `VITE_SUPABASE_URL` | Phase 4 | Phase 4 |
| `VITE_SUPABASE_ANON_KEY` | Phase 4 | Phase 4 |

**Do not set** `VITE_API_PROXY_TARGET` on Vercel — that is dev-only.

### API proxy (same-origin)

`apps/web/vercel.json` already rewrites browser `/api/*` → Fly:

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://signals-lab-api.fly.dev/api/:path*" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Update the Fly hostname when your app name differs. With this setup, use `VITE_API_BASE_URL=/api/v1` so the browser stays same-origin.

### CORS on Fly (required for direct API URL)

If the frontend calls Fly **directly** (no rewrite), add Vercel domains to Fly config:

```yaml
api:
  cors_origins:
    - "https://signals-lab.vercel.app"
    - "https://*.vercel.app"          # preview deployments — tighten in prod
    - "https://your-custom-domain.com"
```

Prefer the **Vercel rewrite** pattern to minimize CORS complexity for read-only dashboard polling.

### Deploy commands

```bash
cd apps/web
npm run build          # verify locally first
vercel                 # first link
vercel --prod          # production
```

Or connect the GitHub repo in the Vercel dashboard with root `apps/web`.

### Acceptance (Phase 3)

- Production URL loads dashboard shell
- Signal feed shows **live** data (not mocks) — remove mock fallback in TanStack Query hooks
- Lighthouse performance ≥ 90 on dashboard shell
- Preview deployments work on PRs

---

## Phase 4 — Supabase (auth & subscriber portal)

Deploy when you need authenticated users beyond yourself.

### Supabase responsibilities

| Feature | Supabase | Fly API |
|---|---|---|
| Sign up / login | ✅ Auth | Validates JWT |
| Role (`researcher`, `consumer`, `admin`) | ✅ `app_metadata` | Maps `sub` → permissions |
| API key storage (hashed) | ✅ Table | Validates key on `/api/v1/*` |
| Signal / feature data | ❌ | ✅ TimescaleDB |

### Supabase setup checklist

- [ ] Create project (same region as Fly if possible)
- [ ] Enable Email + OAuth providers as needed
- [ ] Row Level Security on portal tables only — **not** on signal data in Supabase
- [ ] Set `app_metadata.role` via admin API or signup hook
- [ ] Add Vercel URL to Supabase Auth redirect allow list

### Frontend env (Vercel)

```
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon-key>
```

### Backend (Fly secrets)

```
SUPABASE_JWT_SECRET=<jwt-secret>     # validate Supabase tokens
# or JWKS URL for asymmetric verification
```

FastAPI dependency: verify JWT → load role → enforce publish gate per role (consumer vs researcher).

### Acceptance (Phase 4)

- `/app/*` routes require login
- Researcher sees all confidence bands; consumer sees HIGH/EXTREME only
- API key CRUD in settings creates keys stored hashed in Supabase
- No live trading UI anywhere

---

## Environment variable master table

| Variable | Local | Fly | Vercel | Supabase |
|---|---|---|---|---|
| `SIGNALSLAB_STORAGE__*` | `.env` | secrets | — | — |
| Provider keys (`NEWSAPI_KEY`, …) | `.env` | secrets | — | — |
| `IHABIBI_API_KEY` / `ADMIN_API_KEY` | `.env` | secrets | — | — |
| `VITE_API_BASE_URL` | `.env.local` | — | env | — |
| `VITE_SUPABASE_*` | `.env.local` | — | env | project settings |
| User passwords / JWT | — | — | — | Supabase only |

**Never commit:** `.env`, `.env.local`, `apps/web/.env.local`, Fly secrets exports.

---

## Monitoring & ops (post-deploy)

| Concern | Tool |
|---|---|
| API errors / latency | Fly metrics + `GET /metrics` (Prometheus) |
| Frontend crashes | Sentry (browser SDK in `apps/web/src/main.tsx`) |
| Uptime | Better Stack / Fly checks on `/api/v1/health` |
| Public status page | `/status` route (subset) + full `/app/health` for operators |
| Logs | `fly logs` · structlog JSON on API |

---

## Cost rough order (paid plans you have)

| Service | Idle / dev | Light prod |
|---|---|---|
| **Local + Docker** | $0 | $0 |
| **Fly.io** | ~$0 if stopped | ~$5–30/mo (app + small DB) |
| **Vercel** | $0 hobby / included paid | Included in paid plan |
| **Supabase** | Free tier OK for dev | Paid plan when auth + portal go live |

Start local → add Fly when API works → add Vercel when dashboard needs sharing → add Supabase when you need accounts.

---

## Common mistakes

| Mistake | Fix |
|---|---|
| Deploy Vercel before Fly API | Dashboard shows mocks; waste of time |
| Use Supabase as primary signal DB | Use TimescaleDB on Fly; Supabase is auth/portal only |
| Forget CORS / rewrite | Use Vercel `/api` rewrite **or** add Vercel domain to Fly CORS |
| Skip `web refresh` after pull | Run `signals-lab web refresh` |
| Prod secrets in git | `fly secrets set` + Vercel env UI only |
| Enable live trading in cloud | Out of scope — execution stays downstream |

---

## Related commands

```bash
signals-lab help web
signals-lab web check
signals-lab web docker up
signals-lab health
signals-lab health apis      # no DB required
```

**Script reference:** [scripts/web-dev.sh](../scripts/web-dev.sh) · **Docker:** [docker-compose.yml](../docker-compose.yml)

---

## Roadmap cross-reference

| SPECS milestone | Deployment phase |
|---|---|
| Stage 2 — Feature + signal engine | Phase 1 local only |
| Stage 3 — FastAPI + paper eval + dashboard integration | Phase 2 Fly + Phase 3 Vercel |
| Stage 4 — Calibration + subscriber portal | Phase 4 Supabase + usage metering |
| Future algo feeder | Fly NATS / WebSocket — not Vercel |

---

*Update this doc when `fly.toml`, CI deploy workflows, or Supabase schema land in the repo.*
