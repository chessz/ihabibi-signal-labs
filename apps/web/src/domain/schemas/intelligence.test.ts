import { describe, expect, it } from "vitest";

import { mockIntelligenceFeed } from "@/domain/fixtures/mock-intelligence";
import { intelligenceItemSchema } from "@/domain/schemas/intelligence";

describe("intelligenceItemSchema", () => {
  it("parses mock intelligence feed items", () => {
    for (const item of mockIntelligenceFeed) {
      const parsed = intelligenceItemSchema.parse(item);
      expect(parsed.title.length).toBeGreaterThan(0);
    }
  });
});
