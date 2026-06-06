import { z } from "zod";

export const backtestAssumptionsSchema = z.object({
  entry_model: z.literal("next_bar_open"),
  fee_bps: z.number(),
  slippage_bps: z.number(),
  as_of: z.string(),
});

export const backtestRunSchema = z.object({
  run_id: z.string().uuid(),
  name: z.string(),
  status: z.enum(["queued", "running", "completed", "failed"]),
  created_at: z.string(),
  completed_at: z.string().nullable(),
  assumptions: backtestAssumptionsSchema,
  parameters_version: z.string(),
  metrics: z
    .object({
      hit_rate: z.number(),
      avg_return_pct: z.number(),
      max_drawdown_pct: z.number(),
      trade_count: z.number(),
    })
    .optional(),
  caveats: z.array(z.string()),
});

export type BacktestRun = z.infer<typeof backtestRunSchema>;

export const strategyTestRunSchema = z.object({
  run_id: z.string().uuid(),
  name: z.string(),
  rule_snapshot_id: z.string(),
  status: z.enum(["queued", "running", "completed", "failed"]),
  created_at: z.string(),
  compare_to_run_id: z.string().uuid().optional(),
  metrics: backtestRunSchema.shape.metrics.optional(),
});

export type StrategyTestRun = z.infer<typeof strategyTestRunSchema>;

export const apiKeySchema = z.object({
  key_id: z.string(),
  label: z.string(),
  prefix: z.string(),
  scopes: z.array(z.string()),
  created_at: z.string(),
  last_used_at: z.string().nullable(),
  expires_at: z.string().nullable(),
});

export type ApiKey = z.infer<typeof apiKeySchema>;

export const usageSummarySchema = z.object({
  period_start: z.string(),
  period_end: z.string(),
  requests_total: z.number(),
  requests_limit: z.number(),
  error_count: z.number(),
  top_routes: z.array(z.object({ route: z.string(), count: z.number() })),
});

export type UsageSummary = z.infer<typeof usageSummarySchema>;

export const subscriptionPlanSchema = z.object({
  plan_id: z.string(),
  name: z.string(),
  requests_per_month: z.number(),
  websocket_enabled: z.boolean(),
  history_days: z.number(),
  delay_minutes: z.number(),
});

export type SubscriptionPlan = z.infer<typeof subscriptionPlanSchema>;

export const glossaryTermSchema = z.object({
  id: z.string(),
  term: z.string(),
  short: z.string(),
  long: z.string(),
  related_lesson_slug: z.string().optional(),
});

export type GlossaryTerm = z.infer<typeof glossaryTermSchema>;
