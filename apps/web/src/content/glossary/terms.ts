import type { GlossaryTerm } from "@/domain/schemas/platform";

export const glossaryTerms: GlossaryTerm[] = [
  {
    id: "confidence",
    term: "Confidence",
    short: "How strongly indicators agree on this research idea.",
    long: "A 0–100 score combining weighted technical factors. Bands: LOW, MEDIUM, HIGH, EXTREME. Only HIGH and EXTREME are published externally.",
    related_lesson_slug: "understanding-confidence",
  },
  {
    id: "invalidation",
    term: "Invalidation",
    short: "The condition that would make this signal wrong.",
    long: "A clear, observable rule (e.g. a candle close below a level) that retires the thesis. Not a stop-loss order — research boundary only.",
    related_lesson_slug: "invalidation-and-risk",
  },
  {
    id: "signal",
    term: "Trading signal",
    short: "A research hypothesis about market direction — not an order.",
    long: "signals-lab produces paper-traded ideas with full explainability. Execution happens in separate systems.",
  },
  {
    id: "regime",
    term: "Market regime",
    short: "The current market environment (trending, ranging, volatile).",
    long: "Rules behave differently in different regimes. Signals include regime context for interpretation.",
  },
];

export function getGlossaryTerm(id: string): GlossaryTerm | undefined {
  return glossaryTerms.find((t) => t.id === id);
}
