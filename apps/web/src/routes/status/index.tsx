import { createFileRoute, Link } from "@tanstack/react-router";

import { MarketingShell } from "@/components/layout/AppShell";
import { HealthChip } from "@/components/health/HealthChip";

export const Route = createFileRoute("/status/")({
  component: PublicStatusPage,
});

function PublicStatusPage() {
  return (
    <MarketingShell>
      <div className="mx-auto max-w-2xl px-4 py-12">
        <h1 className="text-2xl font-bold">Public status</h1>
        <p className="mt-2 text-muted-foreground">
          High-level pipeline health. Operators see full detail in the app.
        </p>
        <div className="mt-8 space-y-4 rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <span>Signal API</span>
            <HealthChip status="UP" label="Operational" />
          </div>
          <div className="flex items-center justify-between">
            <span>Market ingest</span>
            <HealthChip status="UP" label="Operational" />
          </div>
          <div className="flex items-center justify-between">
            <span>Social providers</span>
            <HealthChip status="DEGRADED" label="Degraded" />
          </div>
        </div>
        <Link to="/app/health" className="mt-6 inline-block text-sm text-primary underline">
          Full health dashboard (sign in)
        </Link>
      </div>
    </MarketingShell>
  );
}
