import { createFileRoute } from "@tanstack/react-router";

import { HealthChip } from "@/components/health/HealthChip";
import type { ProviderHealth } from "@/domain/schemas/health";

export const Route = createFileRoute("/app/health/")({
  component: HealthPage,
});

const mockProviders: ProviderHealth[] = [
  {
    provider: "binance",
    status: "UP",
    lag_seconds: 42,
    last_success_at: new Date().toISOString(),
    last_error: null,
  },
  {
    provider: "newsapi",
    status: "DEGRADED",
    lag_seconds: 180,
    last_success_at: new Date(Date.now() - 180_000).toISOString(),
    last_error: "Rate limit approaching",
  },
  {
    provider: "lunarcrush",
    status: "DOWN",
    lag_seconds: null,
    last_success_at: null,
    last_error: "HTTP 402 — plan upgrade required",
  },
];

function HealthPage() {
  return (
    <div>
      <header className="mb-6">
        <h1 className="text-2xl font-bold">System health</h1>
        <p className="text-sm text-muted-foreground">
          Upstream providers, pipeline freshness, and API reliability.
        </p>
      </header>

      <div className="mb-6 flex flex-wrap gap-2">
        <HealthChip status="degraded" label="Overall: Degraded" />
        <HealthChip status="UP" label="Ingest: OK" />
        <HealthChip status="DEGRADED" label="Signals: 4m ago" />
      </div>

      <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {mockProviders.map((p) => (
          <li key={p.provider} className="rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold capitalize">{p.provider}</h2>
              <HealthChip status={p.status} label={p.status} />
            </div>
            <dl className="mt-3 space-y-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Lag</dt>
                <dd>{p.lag_seconds != null ? `${p.lag_seconds}s` : "—"}</dd>
              </div>
              {p.last_error && (
                <div>
                  <dt className="text-muted-foreground">Last error</dt>
                  <dd className="text-destructive">{p.last_error}</dd>
                </div>
              )}
            </dl>
          </li>
        ))}
      </ul>
    </div>
  );
}
