import { createFileRoute, Link } from "@tanstack/react-router";

import { ConfidenceBadge } from "@/components/signals/ConfidenceBadge";
import { FreshnessIndicator } from "@/components/signals/FreshnessIndicator";
import { SignalExplainabilityPanel } from "@/components/signals/SignalExplainabilityPanel";
import { SignalNewsPanel } from "@/components/signals/SignalNewsPanel";
import { GlossaryTooltip } from "@/components/glossary/GlossaryTooltip";
import { useSignal } from "@/lib/api/signals";

export const Route = createFileRoute("/app/signals/$signalId")({
  component: SignalDetailPage,
});

function SignalDetailPage() {
  const { signalId } = Route.useParams();
  const { data: signal, isLoading } = useSignal(signalId);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading signal…</p>;
  }

  if (!signal) {
    return (
      <div className="rounded-lg border p-8 text-center">
        <p>Signal not found.</p>
        <Link to="/app/signals" className="mt-4 inline-block text-primary underline">
          Back to signals
        </Link>
      </div>
    );
  }

  const ageSeconds = signal.freshness?.signal_age_seconds ?? 0;
  const linkedNews = signal.linked_intelligence ?? [];

  return (
    <article className="space-y-8">
      <header className="space-y-3 border-b pb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm text-muted-foreground">{signal.asset_pair.exchange}</p>
            <h1 className="text-2xl font-bold">
              {signal.asset_pair.symbol} · {signal.signal_class.replace("_", " ")}
            </h1>
            {signal.narrative_summary && (
              <p className="mt-1 text-sm text-muted-foreground">{signal.narrative_summary}</p>
            )}
          </div>
          <ConfidenceBadge band={signal.confidence_band} score={signal.confidence_score} size="lg" />
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          <FreshnessIndicator ageSeconds={ageSeconds} label="Signal" />
          <span className="text-muted-foreground">Regime: {signal.regime.replace("_", " ")}</span>
          {signal.is_publishable ? (
            <span className="text-success font-medium">Published externally</span>
          ) : (
            <span className="text-warning font-medium">Not published — below HIGH gate</span>
          )}
        </div>
      </header>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Thesis — why this appeared
        </h2>
        <p className="mt-2 text-lg">{signal.thesis}</p>
      </section>

      <SignalNewsPanel items={linkedNews} />

      {signal.beginner_summary && (
        <section className="rounded-lg border border-primary/20 bg-primary/5 p-4">
          <h2 className="text-sm font-semibold">Beginner view</h2>
          <p className="mt-2">{signal.beginner_summary.headline}</p>
          <p className="mt-2 text-sm text-muted-foreground">{signal.beginner_summary.risk_note}</p>
        </section>
      )}

      <SignalExplainabilityPanel
        factors={signal.contributing_factors}
        timeframeAlignment={signal.timeframe_alignment}
      />

      <section className="grid gap-4 md:grid-cols-2">
        <div>
          <h2 className="text-sm font-semibold">
            <GlossaryTooltip termId="invalidation">Invalidation</GlossaryTooltip>
          </h2>
          <p className="mt-2">{signal.invalidation_condition}</p>
        </div>
        <div>
          <h2 className="text-sm font-semibold">Horizon</h2>
          <p className="mt-2">{signal.expected_holding_horizon}</p>
        </div>
      </section>

      {signal.changes_since_previous && (
        <section>
          <h2 className="text-sm font-semibold">What changed since last update</h2>
          <p className="mt-2 text-sm">{signal.changes_since_previous.summary}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Confidence Δ {signal.changes_since_previous.confidence_delta}
          </p>
        </section>
      )}

      <section className="rounded-lg bg-muted/50 p-4 text-xs text-muted-foreground">
        <p>
          Provenance: rule {signal.provenance.rule_version} · features{" "}
          {signal.provenance.computation_version} · {signal.provenance.input_feature_count}{" "}
          inputs · {signal.provenance.data_sources.join(", ")}
          {signal.provenance.intelligence_item_ids &&
            signal.provenance.intelligence_item_ids.length > 0 &&
            ` · ${signal.provenance.intelligence_item_ids.length} intelligence items`}
        </p>
      </section>
    </article>
  );
}
