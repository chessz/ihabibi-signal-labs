import { z } from "zod";

export const providerTierSchema = z.enum(["A", "B", "C"]);
export const intelligenceSourceTypeSchema = z.enum([
  "news",
  "reddit",
  "x",
  "telegram",
  "discord",
  "research",
  "exchange",
  "protocol",
  "market",
  "onchain",
  "influencer",
]);
export const contentRoleSchema = z.enum([
  "primary",
  "commentary",
  "repost",
  "rumor",
]);

export const signalContributionSchema = z.object({
  narrative_class: z.string(),
  weight: z.string(),
  confidence_delta: z.string(),
  explain_snippet: z.string(),
});

export const intelligenceItemSchema = z.object({
  id: z.string().uuid(),
  external_id: z.string(),
  dedup_key: z.string(),
  observed_at: z.string(),
  ingested_at: z.string(),
  provider: z.string(),
  provider_tier: providerTierSchema,
  source_type: intelligenceSourceTypeSchema,
  original_source: z.string(),
  content_role: contentRoleSchema,
  url: z.string().nullable().optional(),
  title: z.string(),
  body: z.string(),
  language: z.string(),
  asset_tags: z.array(z.string()),
  entity_tags: z.array(z.string()),
  sentiment_score: z.string().nullable().optional(),
  credibility_score: z.string(),
  novelty_score: z.string(),
  cross_source_confirmation_count: z.number().int(),
  confirming_providers: z.array(z.string()),
  narrative_cluster_id: z.string().nullable().optional(),
  signal_contribution: signalContributionSchema.nullable().optional(),
});

export type IntelligenceItem = z.infer<typeof intelligenceItemSchema>;

export const linkedIntelligenceSchema = z.object({
  intelligence_id: z.string().uuid(),
  contribution_weight: z.string(),
  confidence_delta: z.string(),
  explain_snippet: z.string(),
  item: intelligenceItemSchema,
});

export type LinkedIntelligence = z.infer<typeof linkedIntelligenceSchema>;

export const intelligenceTickerSchema = z.object({
  schema_version: z.string(),
  generated_at: z.string(),
  items: z.array(intelligenceItemSchema),
});

export const intelligenceFeedSchema = z.object({
  schema_version: z.string(),
  generated_at: z.string(),
  total: z.number(),
  items: z.array(intelligenceItemSchema),
});

export type IntelligenceFeed = z.infer<typeof intelligenceFeedSchema>;

export const intelligenceSignalsSchema = z.object({
  schema_version: z.string(),
  intelligence_id: z.string().uuid(),
  signal_ids: z.array(z.string().uuid()),
});
