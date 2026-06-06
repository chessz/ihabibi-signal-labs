import { createFileRoute } from "@tanstack/react-router";

import { EmptyState } from "@/components/ui/EmptyState";
import { FlaskConical } from "lucide-react";

export const Route = createFileRoute("/app/backtests/")({
  component: BacktestsPage,
});

function BacktestsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Backtesting lab</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Replay historical signals with strict no-look-ahead entry rules. [Stage 3]
      </p>
      <div className="mt-8">
        <EmptyState
          icon={FlaskConical}
          title="No backtest runs yet"
          description="Create a run to replay paper signals over a date range. Entry uses next-bar-open after signal time — never current bar."
        />
      </div>
    </div>
  );
}
