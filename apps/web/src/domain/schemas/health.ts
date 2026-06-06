import { z } from "zod";

export const providerHealthSchema = z.object({
  provider: z.string(),
  status: z.enum(["UP", "DEGRADED", "DOWN", "UNKNOWN"]),
  lag_seconds: z.number().nullable(),
  last_success_at: z.string().nullable(),
  last_error: z.string().nullable(),
  error_rate_1h: z.number().optional(),
});

export type ProviderHealth = z.infer<typeof providerHealthSchema>;

export const aggregatorStatusSchema = z.object({
  name: z.string(),
  providers: z.array(providerHealthSchema),
  overall_status: z.enum(["healthy", "degraded", "outage"]),
  updated_at: z.string(),
});

export type AggregatorStatus = z.infer<typeof aggregatorStatusSchema>;

export const pipelineHealthSchema = z.object({
  last_ingest_at: z.string().nullable(),
  last_feature_run_at: z.string().nullable(),
  last_signal_at: z.string().nullable(),
  publish_queue_depth: z.number(),
  schema_version: z.string(),
});

export type PipelineHealth = z.infer<typeof pipelineHealthSchema>;

export const incidentSchema = z.object({
  incident_id: z.string().uuid(),
  title: z.string(),
  severity: z.enum(["low", "medium", "high", "critical"]),
  status: z.enum(["open", "investigating", "resolved"]),
  started_at: z.string(),
  resolved_at: z.string().nullable(),
  summary: z.string(),
  affected_providers: z.array(z.string()),
});

export type Incident = z.infer<typeof incidentSchema>;

export const healthSnapshotSchema = z.object({
  overall_status: z.enum(["healthy", "degraded", "outage"]),
  providers: z.array(providerHealthSchema),
  pipeline: pipelineHealthSchema,
  api: z.object({
    latency_p95_ms: z.number(),
    error_rate_1h: z.number(),
  }),
  timestamp: z.string(),
});

export type HealthSnapshot = z.infer<typeof healthSnapshotSchema>;
