import { createFileRoute, Link } from "@tanstack/react-router";

import { ConfirmationBadge } from "@/components/intelligence/ConfirmationBadge";
import { IntelligenceCredibilityBar } from "@/components/intelligence/IntelligenceCredibilityBar";
import { useIntelligenceItem, useIntelligenceSignals } from "@/lib/api/intelligence";
import { formatAge } from "@/lib/utils";

export const Route = createFileRoute("/app/intelligence/$itemId")({
  component: IntelligenceDetailPage,
});

function IntelligenceDetailPage() {
  const { itemId } = Route.useParams();
  const { data: item, isLoading } = useIntelligenceItem(itemId);
  const { data: relatedSignals } = useIntelligenceSignals(itemId);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (!item) {
    return (
      <div className="rounded-lg border p-8 text-center">
        <p>Intelligence item not found.</p>
        <Link to="/app/intelligence" className="mt-4 inline-block text-primary underline">
          Back to feed
        </Link>
      </div>
    );
  }

  const ageSeconds = Math.floor(
    (Date.now() - new Date(item.observed_at).getTime()) / 1000,
  );

  return (
    <article className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-3 border-b pb-6">
        <Link to="/app/intelligence" className="text-sm text-primary hover:underline">
          ← Intelligence feed
        </Link>
        <h1 className="text-2xl font-bold">{item.title}</h1>
        <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
          <span>{item.original_source}</span>
          <span>·</span>
          <span>{formatAge(ageSeconds)}</span>
          <span>·</span>
          <span>Tier {item.provider_tier}</span>
          <ConfirmationBadge count={item.cross_source_confirmation_count} />
        </div>
        <div className="flex flex-wrap gap-1">
          {item.asset_tags.map((tag) => (
            <span key={tag} className="rounded bg-muted px-2 py-0.5 text-xs font-mono">
              {tag}
            </span>
          ))}
        </div>
      </header>

      {item.body && <p className="text-foreground/90">{item.body}</p>}

      <IntelligenceCredibilityBar score={item.credibility_score} />

      {item.confirming_providers.length > 1 && (
        <section>
          <h2 className="text-sm font-semibold">Confirming sources</h2>
          <ul className="mt-2 flex flex-wrap gap-2">
            {item.confirming_providers.map((p) => (
              <li key={p} className="rounded border px-2 py-1 text-xs">
                {p}
              </li>
            ))}
          </ul>
        </section>
      )}

      {item.signal_contribution && (
        <section className="rounded-lg border border-primary/20 bg-primary/5 p-4">
          <h2 className="text-sm font-semibold">Signal contribution</h2>
          <p className="mt-2 text-sm">{item.signal_contribution.explain_snippet}</p>
        </section>
      )}

      {relatedSignals && relatedSignals.signal_ids.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold">Related signals</h2>
          <ul className="mt-2 space-y-1">
            {relatedSignals.signal_ids.map((sid) => (
              <li key={sid}>
                <Link
                  to="/app/signals/$signalId"
                  params={{ signalId: sid }}
                  className="text-sm text-primary hover:underline"
                >
                  View signal {sid.slice(0, 8)}…
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block text-sm text-primary hover:underline"
        >
          Read original story →
        </a>
      )}
    </article>
  );
}
