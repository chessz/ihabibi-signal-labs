import { createFileRoute } from "@tanstack/react-router";

import { EmptyState } from "@/components/ui/EmptyState";
import { SlidersHorizontal } from "lucide-react";

export const Route = createFileRoute("/app/strategies/")({
  component: StrategiesPage,
});

function StrategiesPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Strategy testing lab</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Define rule combinations and compare versioned runs. [Stage 3]
      </p>
      <div className="mt-8">
        <EmptyState
          icon={SlidersHorizontal}
          title="No strategy tests yet"
          description="Build a predicate tree from feature conditions, version parameters, and compare outcomes side-by-side."
        />
      </div>
    </div>
  );
}
