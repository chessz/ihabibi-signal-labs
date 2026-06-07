import { createFileRoute } from "@tanstack/react-router";

import { HealthChip } from "@/components/health/HealthChip";
import { useHealthSnapshot } from "@/lib/api/health";

export const Route = createFileRoute("/app/health/")({
  component: HealthPage,
});

function HealthPage() {
  const { data, isLoading } = useHealthSnapshot();
  const providers = data?.providers ?? [];
  const intelligenceProviders = providers.filter((p) =>
    ["rss_fan_in", "cryptocurrency_cv", "newsapi", "lunarcrush"].includes(p.provider),
  );
  const otherProviders = providers.filter(
    (p) => !["rss_fan_in", "cryptocurrency_cv", "newsapi", "lunarcrush"].includes(p.provider),
  );

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-2xl font-bold">System health</h1>
        <p className="text-sm text-muted-foreground">
          Upstream providers, pipeline freshness, and API reliability.
        </p>
      </header>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading health snapshot…</p>
      ) : (
        <>
          <div className="mb-6 flex flex-wrap gap-2">
            <HealthChip
              status={data?.overall_status === "healthy" ? "UP" : "DEGRADED"}
              label={`Overall: ${data?.overall_status ?? "unknown"}`}
            />
          </div>

          <section className="mb-8">
            <h2 className="mb-4 text-lg font-semibold">Intelligence pipeline</h2>
            <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {intelligenceProviders.map((p) => (
                <li key={p.provider} className="rounded-lg border p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{p.provider}</h3>
                    <HealthChip status={p.status} label={p.status} />
                  </div>
                  {"tier" in p && p.tier && (
                    <p className="mt-1 text-xs text-muted-foreground">Tier {p.tier}</p>
                  )}
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
          </section>

          <section>
            <h2 className="mb-4 text-lg font-semibold">Market & other providers</h2>
            <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {otherProviders.map((p) => (
                <li key={p.provider} className="rounded-lg border p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold capitalize">{p.provider}</h3>
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
          </section>
        </>
      )}
    </div>
  );
}
