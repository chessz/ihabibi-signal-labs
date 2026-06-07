# signals-lab Web Dashboard

React + TypeScript frontend for the signals-lab research platform.

**Stack:** Vite · TanStack Router · TanStack Query · Tailwind v4 · Supabase Auth (Stage 3)

**Full product/UX plan:** [`docs/FRONTEND_PRODUCT_PLAN.md`](../../docs/FRONTEND_PRODUCT_PLAN.md)  
**Deployment (when to use Vercel / Fly / Supabase):** [`docs/DEPLOYMENT.md`](../../docs/DEPLOYMENT.md)

## Quick start

```bash
# From repo root (recommended)
export PATH="$(pwd)/bin:$PATH"
signals-lab web setup              # npm install + .env.local
signals-lab web dev                # http://localhost:5173

# After git pull or when deps/env change:
signals-lab web refresh
signals-lab web refresh --docker   # also restart Postgres container
signals-lab web refresh --force    # reinstall + clear Vite cache
```

Or use the script directly: `./scripts/web-dev.sh refresh`

**Local database (optional, for ingestion):**

```bash
signals-lab web docker up          # TimescaleDB on localhost:5432
```

Manual path:

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

## Routes (MVP scaffold)

| Route | Access | Purpose |
|---|---|---|
| `/` | Public | Marketing homepage |
| `/academy` | Public | Education / glossary |
| `/status` | Public | Public status strip |
| `/app/signals` | Auth (TODO) | Signal explorer |
| `/app/signals/:id` | Auth | Signal detail |
| `/app/health` | Auth | Provider & pipeline health |
| `/app/backtests` | Auth | Backtesting lab [Stage 3] |
| `/app/strategies` | Auth | Strategy lab [Stage 3] |
| `/app/settings` | Auth | Preferences, API keys |

## Project structure

```
src/
├── routes/              # TanStack Router (file-based)
├── features/            # Feature modules (hooks, pages logic) — expand in Stage 3
├── components/
│   ├── signals/         # SignalCard, ConfidenceBadge, etc.
│   ├── health/
│   ├── glossary/
│   ├── layout/
│   └── ui/
├── domain/
│   ├── schemas/         # Zod types mirroring FastAPI
│   └── fixtures/        # Mock data until API live
├── lib/
│   ├── api/             # apiFetch client
│   └── supabase/
└── content/glossary/
```

## Deployment

- **Vercel:** deploy `apps/web` as static SPA; rewrite `/api/*` to Fly.io FastAPI
- **Fly.io:** Python API + workers (separate from this app)
- **Supabase:** Auth + user/org metadata

See `vercel.json` for SPA fallback rewrites.

## Environment

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | FastAPI base (default `/api/v1` via proxy) |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |

## Why Vite (not Next.js)

Dashboard-first product with API on Fly.io. Vite = smallest ops surface, best chart/table perf.
Switch to Next.js when Academy SEO becomes a primary acquisition channel or you need edge middleware on the same origin.

## Tests

```bash
npm run test
```
