import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { IntelligenceCard } from "@/components/intelligence/IntelligenceCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { useIntelligenceFeed } from "@/lib/api/intelligence";
import { Newspaper } from "lucide-react";

export const Route = createFileRoute("/app/intelligence/")({
  component: IntelligenceFeedPage,
});

function IntelligenceFeedPage() {
  const [asset, setAsset] = useState("");
  const [confirmedOnly, setConfirmedOnly] = useState(false);
  const { data, isLoading, isError } = useIntelligenceFeed({
    asset: asset || undefined,
    confirmedOnly,
    limit: 50,
  });

  const items = data?.items ?? [];

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Intelligence feed</h1>
        <p className="text-sm text-muted-foreground">
          Tier A news and narratives — deduplicated, scored, and linked to signals.
        </p>
      </header>

      <div className="mb-6 flex flex-wrap gap-4">
        <label className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Asset</span>
          <select
            value={asset}
            onChange={(e) => setAsset(e.target.value)}
            className="rounded border px-2 py-1"
          >
            <option value="">All</option>
            <option value="BTC">BTC</option>
            <option value="ETH">ETH</option>
            <option value="SOL">SOL</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={confirmedOnly}
            onChange={(e) => setConfirmedOnly(e.target.checked)}
          />
          Confirmed only (≥2 sources)
        </label>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading feed…</p>}
      {isError && (
        <p className="text-sm text-destructive">Failed to load intelligence feed.</p>
      )}

      {!isLoading && items.length === 0 ? (
        <EmptyState
          icon={Newspaper}
          title="No intelligence items"
          description="Try widening filters or check provider health."
        />
      ) : (
        <ul className="grid gap-4 md:grid-cols-2">
          {items.map((item) => (
            <li key={item.id}>
              <IntelligenceCard item={item} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
