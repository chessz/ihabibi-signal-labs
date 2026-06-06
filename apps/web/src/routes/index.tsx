import { createFileRoute, Link } from "@tanstack/react-router";

import { MarketingShell } from "@/components/layout/AppShell";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  return (
    <MarketingShell>
      <section className="mx-auto max-w-6xl px-4 py-20">
        <p className="text-sm font-medium text-primary">iHabibi Signal Research</p>
        <h1 className="mt-4 max-w-2xl text-4xl font-bold tracking-tight">
          Explainable crypto signals — paper research, zero look-ahead
        </h1>
        <p className="mt-4 max-w-xl text-lg text-muted-foreground">
          signals-lab ingests market data, computes versioned features, and publishes
          HIGH-confidence research ideas for iHabibi Trading and future algo feeders.
          No live trading. Full provenance.
        </p>
        <div className="mt-8 flex flex-wrap gap-4">
          <Link
            to="/app/signals"
            className="rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground"
          >
            Explore signals
          </Link>
          <Link
            to="/academy"
            className="rounded-md border px-5 py-2.5 text-sm font-medium hover:bg-muted"
          >
            Start learning
          </Link>
        </div>
        <dl className="mt-16 grid gap-6 sm:grid-cols-3">
          {[
            ["5 min", "Signal generation cadence"],
            ["< 60s", "Market ingest freshness target"],
            ["HIGH+", "External publish gate only"],
          ].map(([value, label]) => (
            <div key={label} className="rounded-lg border p-4">
              <dt className="text-2xl font-bold">{value}</dt>
              <dd className="mt-1 text-sm text-muted-foreground">{label}</dd>
            </div>
          ))}
        </dl>
      </section>
    </MarketingShell>
  );
}
