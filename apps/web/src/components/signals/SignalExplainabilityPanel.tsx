import type { ContributingFactor } from "@/domain/schemas/signal";
import { GlossaryTooltip } from "@/components/glossary/GlossaryTooltip";

type Props = {
  factors: ContributingFactor[];
  timeframeAlignment?: Record<string, string>;
};

export function SignalExplainabilityPanel({ factors, timeframeAlignment }: Props) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section aria-labelledby="factors-heading">
        <h3 id="factors-heading" className="text-sm font-semibold">
          <GlossaryTooltip termId="signal">Confluence factors</GlossaryTooltip>
        </h3>
        <ul className="mt-3 space-y-2">
          {factors.length === 0 ? (
            <li className="text-sm text-muted-foreground">No factors recorded.</li>
          ) : (
            factors.map((f) => (
              <li
                key={`${f.feature_family}-${f.feature_name}`}
                className="rounded-md border px-3 py-2 text-sm"
              >
                <div className="flex justify-between gap-2">
                  <span className="font-medium">
                    {f.feature_family}.{f.feature_name}
                  </span>
                  <span className="capitalize text-muted-foreground">{f.direction}</span>
                </div>
                <p className="mt-1 text-muted-foreground">{f.description}</p>
              </li>
            ))
          )}
        </ul>
      </section>

      {timeframeAlignment && (
        <section aria-labelledby="timeframe-heading">
          <h3 id="timeframe-heading" className="text-sm font-semibold">
            Timeframe alignment
          </h3>
          <ul className="mt-3 space-y-2">
            {Object.entries(timeframeAlignment).map(([tf, dir]) => (
              <li key={tf} className="flex items-center justify-between text-sm">
                <span className="font-mono">{tf}</span>
                <span className="capitalize">{dir}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
