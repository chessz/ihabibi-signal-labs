import { z } from "zod";

export const confidenceBandSchema = z.enum([
  "LOW",
  "MEDIUM",
  "HIGH",
  "EXTREME",
]);

export const signalClassSchema = z.enum([
  "LONG_CANDIDATE",
  "SHORT_CANDIDATE",
  "WATCH",
  "EXIT_LONG",
  "EXIT_SHORT",
]);

export const signalSideSchema = z.enum(["BUY", "SELL", "HOLD"]);

export const marketRegimeSchema = z.enum([
  "TRENDING_UP",
  "TRENDING_DOWN",
  "RANGING",
  "HIGH_VOLATILITY",
  "UNKNOWN",
]);

export const assetPairSchema = z.object({
  symbol: z.string(),
  base: z.string(),
  quote: z.string(),
  exchange: z.string(),
});

export const contributingFactorSchema = z.object({
  feature_family: z.string(),
  feature_name: z.string(),
  value: z.string(),
  weight: z.string(),
  direction: z.enum(["bullish", "bearish", "neutral"]),
  description: z.string(),
  z_score: z.string().optional(),
});

export const provenanceSchema = z.object({
  data_sources: z.array(z.string()),
  observation_window: z.string(),
  computation_version: z.string(),
  rule_version: z.string(),
  generated_by: z.string(),
  input_feature_count: z.number(),
  computation_time_ms: z.number().optional(),
});

export const signalSchema = z.object({
  signal_id: z.string().uuid(),
  dedup_key: z.string().uuid().optional(),
  asset_pair: assetPairSchema,
  signal_class: signalClassSchema,
  side: signalSideSchema,
  confidence_score: z.string(),
  confidence_band: confidenceBandSchema,
  is_publishable: z.boolean(),
  generated_at: z.string(),
  expiry_at: z.string().optional(),
  regime: marketRegimeSchema,
  thesis: z.string(),
  invalidation_condition: z.string(),
  expected_holding_horizon: z.string(),
  entry_price: z.string().optional(),
  target_price: z.string().optional(),
  contributing_factors: z.array(contributingFactorSchema),
  timeframe_alignment: z.record(z.string(), z.string()).optional(),
  freshness: z
    .object({
      market_data_age_seconds: z.number(),
      feature_computed_age_seconds: z.number(),
      signal_age_seconds: z.number(),
    })
    .optional(),
  provenance: provenanceSchema,
  changes_since_previous: z
    .object({
      previous_signal_id: z.string().uuid(),
      confidence_delta: z.string(),
      summary: z.string(),
    })
    .optional(),
  beginner_summary: z
    .object({
      headline: z.string(),
      risk_note: z.string(),
      confidence_plain: z.string(),
    })
    .optional(),
  status: z.enum(["ACTIVE", "EXPIRED", "INVALIDATED", "CLOSED"]),
  schema_version: z.string().optional(),
});

export type Signal = z.infer<typeof signalSchema>;
export type ConfidenceBand = z.infer<typeof confidenceBandSchema>;
export type ContributingFactor = z.infer<typeof contributingFactorSchema>;

export const signalListItemSchema = signalSchema.pick({
  signal_id: true,
  asset_pair: true,
  signal_class: true,
  side: true,
  confidence_band: true,
  confidence_score: true,
  generated_at: true,
  is_publishable: true,
  regime: true,
  thesis: true,
});

export type SignalListItem = z.infer<typeof signalListItemSchema>;

export const signalExplanationSchema = z.object({
  signal_id: z.string().uuid(),
  why_appeared: z.string(),
  why_not_published: z.string().optional(),
  factor_summary: z.array(
    z.object({
      label: z.string(),
      direction: z.string(),
      weight: z.string(),
    }),
  ),
  beginner_translation: z.string().optional(),
});

export type SignalExplanation = z.infer<typeof signalExplanationSchema>;

export const signalVersionSchema = z.object({
  signal_id: z.string().uuid(),
  version: z.string(),
  rule_version: z.string(),
  computation_version: z.string(),
  changed_at: z.string(),
  diff_summary: z.string(),
});

export type SignalVersion = z.infer<typeof signalVersionSchema>;
