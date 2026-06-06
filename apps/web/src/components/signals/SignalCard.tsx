import { Link } from "@tanstack/react-router";

import { ConfidenceBadge } from "@/components/signals/ConfidenceBadge";
import { FreshnessIndicator } from "@/components/signals/FreshnessIndicator";
import type { SignalListItem } from "@/domain/schemas/signal";
import { cn } from "@/lib/utils";

type Props = {
  signal: SignalListItem;
  compact?: boolean;
  showBeginner?: boolean;
  className?: string;
};

export function SignalCard({ signal, compact, showBeginner, className }: Props) {
  const ageSeconds = Math.floor(
    (Date.now() - new Date(signal.generated_at).getTime()) / 1000,
  );

  return (
    <article
      className={cn(
        "rounded-lg border bg-white p-4 shadow-sm transition hover:border-primary/30",
        className,
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <Link
            to="/app/signals/$signalId"
            params={{ signalId: signal.signal_id }}
            className="text-base font-semibold hover:underline"
          >
            {signal.asset_pair.symbol}
          </Link>
          <p className="text-xs text-muted-foreground">
            {signal.signal_class.replace("_", " ")} · {signal.regime.replace("_", " ")}
          </p>
        </div>
        <ConfidenceBadge band={signal.confidence_band} score={signal.confidence_score} />
      </div>

      {!compact && (
        <p className="mt-3 text-sm text-foreground/90 line-clamp-2">{signal.thesis}</p>
      )}

      {showBeginner && (
        <p className="mt-2 text-xs text-muted-foreground italic">
          Research idea only — not financial advice or an order to trade.
        </p>
      )}

      <div className="mt-3 flex items-center justify-between">
        <FreshnessIndicator ageSeconds={ageSeconds} />
        {!signal.is_publishable && (
          <span className="text-xs text-muted-foreground">Internal only</span>
        )}
      </div>
    </article>
  );
}

export function SignalCardSkeleton() {
  return (
    <div className="animate-pulse rounded-lg border p-4" aria-busy="true">
      <div className="h-4 w-1/3 rounded bg-muted" />
      <div className="mt-3 h-3 w-full rounded bg-muted" />
      <div className="mt-2 h-3 w-2/3 rounded bg-muted" />
    </div>
  );
}
