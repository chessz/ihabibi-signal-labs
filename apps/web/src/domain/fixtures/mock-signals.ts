import type { Signal } from "@/domain/schemas/signal";

export const mockSignals: Signal[] = [
  {
    signal_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    dedup_key: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    asset_pair: {
      symbol: "BTC/USDT",
      base: "BTC",
      quote: "USDT",
      exchange: "binance",
    },
    signal_class: "LONG_CANDIDATE",
    side: "BUY",
    confidence_score: "78",
    confidence_band: "HIGH",
    is_publishable: true,
    generated_at: new Date(Date.now() - 4 * 60_000).toISOString(),
    expiry_at: new Date(Date.now() + 4 * 60 * 60_000).toISOString(),
    regime: "TRENDING_UP",
    thesis:
      "Momentum + trend alignment: 4h close above 50 EMA, RSI 62, MACD bullish cross on 1h. Institutional BTC narratives add fundamental support.",
    narrative_summary: "Institutional BTC accumulation + native yield narrative",
    invalidation_condition: "4h close below 50 EMA",
    expected_holding_horizon: "4h",
    entry_price: "67250.00",
    target_price: "70100.00",
    contributing_factors: [
      {
        feature_family: "trend",
        feature_name: "sma_50_distance",
        value: "0.012",
        weight: "0.25",
        direction: "bullish",
        description: "Price 1.2% above 50-period SMA on 4h",
        z_score: "1.4",
      },
      {
        feature_family: "momentum",
        feature_name: "rsi_14",
        value: "62",
        weight: "0.20",
        direction: "bullish",
        description: "RSI in bullish zone without overbought extreme",
      },
    ],
    timeframe_alignment: { "1h": "bullish", "4h": "bullish", "1d": "neutral" },
    freshness: {
      market_data_age_seconds: 42,
      feature_computed_age_seconds: 240,
      signal_age_seconds: 240,
    },
    provenance: {
      data_sources: ["binance"],
      observation_window: "24h",
      computation_version: "1.0.0",
      rule_version: "v1.2.0",
      generated_by: "signal-engine",
      input_feature_count: 14,
      computation_time_ms: 87,
    },
    changes_since_previous: {
      previous_signal_id: "990e8400-e29b-41d4-a716-446655440000",
      confidence_delta: "6",
      summary: "RSI crossed 60; new 4h bar confirmed trend",
    },
    beginner_summary: {
      headline:
        "Research suggests upward bias for BTC over the next few hours.",
      risk_note:
        "Paper research only. Not financial advice. Signal can fail if price closes below support.",
      confidence_plain:
        "Fairly strong agreement across indicators, but not guaranteed.",
    },
    status: "ACTIVE",
    schema_version: "1.0.0",
  },
  {
    signal_id: "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    asset_pair: {
      symbol: "ETH/USDT",
      base: "ETH",
      quote: "USDT",
      exchange: "binance",
    },
    signal_class: "WATCH",
    side: "HOLD",
    confidence_score: "58",
    confidence_band: "MEDIUM",
    is_publishable: false,
    generated_at: new Date(Date.now() - 12 * 60_000).toISOString(),
    regime: "RANGING",
    thesis: "Mixed momentum; waiting for breakout confirmation above range high.",
    narrative_summary: "ETH derivatives positioning narrative",
    invalidation_condition: "Close below range low on 4h",
    expected_holding_horizon: "8h",
    contributing_factors: [],
    provenance: {
      data_sources: ["binance"],
      observation_window: "24h",
      computation_version: "1.0.0",
      rule_version: "v1.2.0",
      generated_by: "signal-engine",
      input_feature_count: 12,
    },
    status: "ACTIVE",
  },
];

export function getMockSignal(id: string): Signal | undefined {
  return mockSignals.find((s) => s.signal_id === id);
}
