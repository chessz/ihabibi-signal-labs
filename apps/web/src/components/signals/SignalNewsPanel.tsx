import { Link } from "@tanstack/react-router";
import { ExternalLink, Newspaper } from "lucide-react";

import { ConfirmationBadge } from "@/components/intelligence/ConfirmationBadge";
import { GlossaryTooltip } from "@/components/glossary/GlossaryTooltip";
import type { LinkedIntelligence } from "@/domain/schemas/intelligence";
import { formatAge } from "@/lib/utils";

type Props = {
  items: LinkedIntelligence[];
  showConfidenceDelta?: boolean;
};

export function SignalNewsPanel({ items, showConfidenceDelta = true }: Props) {
  return (
    <section aria-labelledby="news-context-heading" className="rounded-lg border p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 id="news-context-heading" className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          <Newspaper className="size-4" aria-hidden />
          <GlossaryTooltip termId="narrative-catalyst">News & narrative context</GlossaryTooltip>
        </h2>
        {items.length > 0 && (
          <span className="text-xs text-muted-foreground">{items.length} linked</span>
        )}
      </div>

      {items.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">
          No narrative catalyst linked — this signal is driven by technical factors only.
        </p>
      ) : (
        <ul className="mt-4 space-y-4">
          {items.map((link) => {
            const ageSeconds = Math.floor(
              (Date.now() - new Date(link.item.observed_at).getTime()) / 1000,
            );
            const isRumor = link.item.content_role === "rumor";
            return (
              <li key={link.intelligence_id} className="border-l-2 border-primary/30 pl-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="font-medium">{link.item.title}</p>
                  {isRumor && (
                    <span className="text-xs text-warning" title="Unconfirmed rumor">
                      ⚠ Rumor
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {link.item.original_source} · {formatAge(ageSeconds)} · credibility{" "}
                  {Math.round(Number(link.item.credibility_score) * 100)}%
                  <ConfirmationBadge
                    count={link.item.cross_source_confirmation_count}
                    className="ml-2"
                  />
                </p>
                <p className="mt-2 text-sm">
                  →{" "}
                  {showConfidenceDelta && (
                    <span className="font-medium text-primary">
                      +{link.confidence_delta} confidence:{" "}
                    </span>
                  )}
                  {link.explain_snippet}
                </p>
                <div className="mt-2 flex flex-wrap gap-3 text-xs">
                  {link.item.url && (
                    <a
                      href={link.item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-primary hover:underline"
                    >
                      View story <ExternalLink className="size-3" aria-hidden />
                    </a>
                  )}
                  <Link
                    to="/app/intelligence/$itemId"
                    params={{ itemId: link.intelligence_id }}
                    className="text-primary hover:underline"
                  >
                    View intelligence record
                  </Link>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
