import { Link } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";

import { ConfirmationBadge } from "@/components/intelligence/ConfirmationBadge";
import { IntelligenceCredibilityBar } from "@/components/intelligence/IntelligenceCredibilityBar";
import type { IntelligenceItem } from "@/domain/schemas/intelligence";
import { formatAge } from "@/lib/utils";
import { cn } from "@/lib/utils";

type Props = {
  item: IntelligenceItem;
  compact?: boolean;
  className?: string;
};

export function IntelligenceCard({ item, compact, className }: Props) {
  const ageSeconds = Math.floor(
    (Date.now() - new Date(item.observed_at).getTime()) / 1000,
  );
  const isRumor = item.content_role === "rumor";

  return (
    <article className={cn("rounded-lg border bg-white p-4 shadow-sm", className)}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <Link
            to="/app/intelligence/$itemId"
            params={{ itemId: item.id }}
            className="font-semibold hover:underline line-clamp-2"
          >
            {item.title}
          </Link>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.original_source} · {formatAge(ageSeconds)}
          </p>
        </div>
        <div className="flex flex-wrap gap-1">
          {isRumor && (
            <span className="rounded bg-warning/15 px-2 py-0.5 text-xs text-warning" title="Unconfirmed rumor">
              ⚠ Rumor
            </span>
          )}
          <ConfirmationBadge count={item.cross_source_confirmation_count} />
        </div>
      </div>

      {!compact && item.body && (
        <p className="mt-3 text-sm text-muted-foreground line-clamp-2">{item.body}</p>
      )}

      <div className="mt-3 flex flex-wrap gap-1">
        {item.asset_tags.map((tag) => (
          <span key={tag} className="rounded bg-muted px-2 py-0.5 text-xs font-mono">
            {tag}
          </span>
        ))}
      </div>

      {!compact && (
        <div className="mt-3">
          <IntelligenceCredibilityBar score={item.credibility_score} />
        </div>
      )}

      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          View original <ExternalLink className="size-3" aria-hidden />
        </a>
      )}
    </article>
  );
}
