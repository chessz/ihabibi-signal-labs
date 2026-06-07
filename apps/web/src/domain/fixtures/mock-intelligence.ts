import type { IntelligenceItem, LinkedIntelligence } from "@/domain/schemas/intelligence";

const now = Date.now();

function hoursAgo(h: number): string {
  return new Date(now - h * 60 * 60 * 1000).toISOString();
}

export const MOCK_INTEL_IDS = {
  btcStrategy: "f1111111-1111-4111-8111-111111111111",
  btcYield: "f2222222-2222-4222-8222-222222222222",
  ethDerivatives: "f3333333-3333-4333-8333-333333333333",
  ethEtf: "f4444444-4444-4444-8444-444444444444",
  venezuelaStable: "f5555555-5555-4555-8555-555555555555",
  depinGaming: "f6666666-6666-4666-8666-666666666666",
} as const;

export const mockIntelligenceFeed: IntelligenceItem[] = [
  {
    id: MOCK_INTEL_IDS.btcStrategy,
    external_id: "seed:btc-strategy",
    dedup_key: "title:seed-btc-strategy",
    observed_at: hoursAgo(3),
    ingested_at: new Date(now).toISOString(),
    provider: "rss_fan_in",
    provider_tier: "A",
    source_type: "news",
    original_source: "Blockworks",
    content_role: "primary",
    title: "The Strategy playbook looks different in 2026",
    body: "Institutional BTC accumulation strategies are shifting as macro conditions evolve.",
    language: "en",
    asset_tags: ["BTC"],
    entity_tags: [],
    credibility_score: "0.85",
    novelty_score: "0.72",
    cross_source_confirmation_count: 1,
    confirming_providers: ["rss_fan_in"],
    signal_contribution: {
      narrative_class: "research_grade_development",
      weight: "0.15",
      confidence_delta: "5",
      explain_snippet: "Institutional accumulation narrative supports trend continuation",
    },
  },
  {
    id: MOCK_INTEL_IDS.btcYield,
    external_id: "seed:btc-yield",
    dedup_key: "title:seed-btc-yield",
    observed_at: hoursAgo(5),
    ingested_at: new Date(now).toISOString(),
    provider: "rss_fan_in",
    provider_tier: "A",
    source_type: "news",
    original_source: "Blockworks",
    content_role: "primary",
    title: "Yield Basis is making native BTC yield a reality",
    body: "Native BTC yield products are gaining traction among DeFi participants.",
    language: "en",
    asset_tags: ["BTC"],
    entity_tags: [],
    credibility_score: "0.85",
    novelty_score: "0.68",
    cross_source_confirmation_count: 1,
    confirming_providers: ["rss_fan_in"],
    signal_contribution: {
      narrative_class: "research_grade_development",
      weight: "0.10",
      confidence_delta: "3",
      explain_snippet: "Fundamental DeFi narrative adds medium-term bid support",
    },
  },
  {
    id: MOCK_INTEL_IDS.ethDerivatives,
    external_id: "seed:eth-derivatives",
    dedup_key: "title:seed-eth-derivatives",
    observed_at: hoursAgo(4),
    ingested_at: new Date(now).toISOString(),
    provider: "rss_fan_in",
    provider_tier: "A",
    source_type: "news",
    original_source: "Blockworks",
    content_role: "primary",
    title: "ETH derivatives reset and the next retail trade",
    body: "ETH derivatives open interest reset may set up the next directional move.",
    language: "en",
    asset_tags: ["ETH"],
    entity_tags: [],
    credibility_score: "0.85",
    novelty_score: "0.70",
    cross_source_confirmation_count: 1,
    confirming_providers: ["rss_fan_in"],
    signal_contribution: {
      narrative_class: "narrative_emerging",
      weight: "0.12",
      confidence_delta: "4",
      explain_snippet: "Derivatives positioning narrative aligns with range breakout watch",
    },
  },
  {
    id: MOCK_INTEL_IDS.ethEtf,
    external_id: "seed:eth-etf",
    dedup_key: "title:seed-eth-etf",
    observed_at: hoursAgo(2),
    ingested_at: new Date(now).toISOString(),
    provider: "rss_fan_in",
    provider_tier: "A",
    source_type: "news",
    original_source: "The Block",
    content_role: "primary",
    title: "Spot ETH ETF sees record inflows",
    body: "Spot ETH ETF products recorded their largest weekly inflows to date.",
    language: "en",
    asset_tags: ["ETH", "BTC"],
    entity_tags: ["BlackRock", "SEC"],
    credibility_score: "0.85",
    novelty_score: "0.78",
    cross_source_confirmation_count: 4,
    confirming_providers: ["rss_fan_in", "rss_coindesk", "rss_cointelegraph", "rss_blockworks"],
    signal_contribution: {
      narrative_class: "market_confirmed_breakout_catalyst",
      weight: "0.22",
      confidence_delta: "8",
      explain_snippet: "ETF inflows confirmed by 4 independent sources",
    },
  },
  {
    id: MOCK_INTEL_IDS.venezuelaStable,
    external_id: "seed:venezuela",
    dedup_key: "title:seed-venezuela",
    observed_at: hoursAgo(1.5),
    ingested_at: new Date(now).toISOString(),
    provider: "rss_fan_in",
    provider_tier: "A",
    source_type: "news",
    original_source: "Blockworks",
    content_role: "primary",
    title: "Venezuela's sanctions are stablecoins' proof of concept",
    body: "",
    language: "en",
    asset_tags: [],
    entity_tags: [],
    credibility_score: "0.85",
    novelty_score: "0.65",
    cross_source_confirmation_count: 1,
    confirming_providers: ["rss_fan_in"],
  },
  {
    id: MOCK_INTEL_IDS.depinGaming,
    external_id: "seed:depin",
    dedup_key: "title:seed-depin",
    observed_at: hoursAgo(6),
    ingested_at: new Date(now).toISOString(),
    provider: "rss_fan_in",
    provider_tier: "A",
    source_type: "news",
    original_source: "Blockworks",
    content_role: "primary",
    title: "DePIN and crypto gaming led a surprising end-of-year rebound",
    body: "",
    language: "en",
    asset_tags: ["BTC"],
    entity_tags: [],
    credibility_score: "0.85",
    novelty_score: "0.60",
    cross_source_confirmation_count: 1,
    confirming_providers: ["rss_fan_in"],
  },
];

export const mockLinkedIntelligenceBySignalId: Record<string, LinkedIntelligence[]> = {
  "a1b2c3d4-e5f6-7890-abcd-ef1234567890": [
    {
      intelligence_id: MOCK_INTEL_IDS.btcStrategy,
      contribution_weight: "0.15",
      confidence_delta: "5",
      explain_snippet: "Institutional accumulation narrative supports trend continuation",
      item: mockIntelligenceFeed[0]!,
    },
    {
      intelligence_id: MOCK_INTEL_IDS.btcYield,
      contribution_weight: "0.10",
      confidence_delta: "3",
      explain_snippet: "Fundamental DeFi narrative adds medium-term bid support",
      item: mockIntelligenceFeed[1]!,
    },
  ],
  "b2c3d4e5-f6a7-8901-bcde-f12345678901": [
    {
      intelligence_id: MOCK_INTEL_IDS.ethDerivatives,
      contribution_weight: "0.12",
      confidence_delta: "4",
      explain_snippet: "Derivatives positioning narrative aligns with range breakout watch",
      item: mockIntelligenceFeed[2]!,
    },
  ],
};

export function getMockIntelligenceItem(id: string): IntelligenceItem | undefined {
  return mockIntelligenceFeed.find((item) => item.id === id);
}

export function getMockTickerItems(limit = 12): IntelligenceItem[] {
  return [...mockIntelligenceFeed]
    .sort((a, b) => {
      const confA = a.cross_source_confirmation_count >= 2 ? 1 : 0;
      const confB = b.cross_source_confirmation_count >= 2 ? 1 : 0;
      if (confB !== confA) return confB - confA;
      return new Date(b.observed_at).getTime() - new Date(a.observed_at).getTime();
    })
    .slice(0, limit);
}
