import { createFileRoute } from "@tanstack/react-router";

import { SignalCard } from "@/components/signals/SignalCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { mockSignals } from "@/domain/fixtures/mock-signals";
import { Radio } from "lucide-react";

export const Route = createFileRoute("/app/signals/")({
  component: SignalsPage,
});

function SignalsPage() {
  // TODO [Stage 3]: Replace with useSignals() TanStack Query hook
  const publishableOnly = false;
  const signals = publishableOnly
    ? mockSignals.filter((s) => s.is_publishable)
    : mockSignals;

  return (
    <div>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Signal explorer</h1>
          <p className="text-sm text-muted-foreground">
            Research candidates with full explainability. External consumers see HIGH/EXTREME
            only.
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" disabled className="rounded" />
          Beginner mode
        </label>
      </header>

      {signals.length === 0 ? (
        <EmptyState
          icon={Radio}
          title="No signals in this view"
          description="The pipeline is healthy but no signals match your filters. Try widening the confidence band or check health status."
        />
      ) : (
        <ul className="grid gap-4 md:grid-cols-2">
          {signals.map((signal) => (
            <li key={signal.signal_id}>
              <SignalCard signal={signal} showBeginner />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
