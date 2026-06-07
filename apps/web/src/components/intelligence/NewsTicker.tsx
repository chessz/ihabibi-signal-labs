import { Link } from "@tanstack/react-router";
import { Newspaper } from "lucide-react";

import { useIntelligenceTicker } from "@/lib/api/intelligence";
import { formatAge } from "@/lib/utils";
import { cn } from "@/lib/utils";

export function NewsTicker() {
  const { data, isLoading, isError } = useIntelligenceTicker(12);
  const items = data?.items ?? [];
  const lastRefresh = data?.generated_at;
  const isLive =
    lastRefresh != null && Date.now() - new Date(lastRefresh).getTime() < 5 * 60 * 1000;

  if (isLoading) {
    return (
      <div className="border-b bg-muted/30 px-4 py-2 text-xs text-muted-foreground" aria-busy="true">
        Loading intelligence feed…
      </div>
    );
  }

  if (isError || items.length === 0) {
    return (
      <div className="border-b bg-muted/30 px-4 py-2 text-xs text-muted-foreground">
        No recent intelligence —{" "}
        <Link to="/app/health" className="underline">
          check health
        </Link>
      </div>
    );
  }

  return (
    <div
      className="border-b bg-muted/30"
      role="region"
      aria-label="Live crypto news ticker"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-2">
        <span
          className={cn(
            "shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide",
            isLive ? "bg-success/15 text-success" : "bg-warning/15 text-warning",
          )}
        >
          {isLive ? "Live" : "Delayed"}
        </span>
        <Newspaper className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
        <div className="min-w-0 flex-1 overflow-hidden">
          <ul
            className={cn(
              "flex gap-8 whitespace-nowrap text-xs",
              "motion-safe:animate-[ticker_40s_linear_infinite]",
              "motion-reduce:flex-wrap motion-reduce:whitespace-normal motion-reduce:gap-2",
            )}
          >
            {[...items, ...items].map((item, idx) => {
              const ageSeconds = Math.floor(
                (Date.now() - new Date(item.observed_at).getTime()) / 1000,
              );
              return (
                <li key={`${item.id}-${idx}`} className="inline-flex items-center gap-2">
                  <Link
                    to="/app/intelligence/$itemId"
                    params={{ itemId: item.id }}
                    className="hover:text-primary hover:underline"
                  >
                    {item.title}
                  </Link>
                  <span className="text-muted-foreground">
                    — {item.original_source}
                    {item.cross_source_confirmation_count >= 2 &&
                      ` (${item.cross_source_confirmation_count} sources)`}
                    {item.asset_tags[0] && ` · ${item.asset_tags[0]}`}
                    · {formatAge(ageSeconds)}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}
