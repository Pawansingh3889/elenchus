import { render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";

import { LensStripView } from "@/components/lens/LensStripView";
import { lensStripSchema } from "@/lib/schemas";

test.each([
  { cached: null, missing: 2, expected: "not reported" },
  { cached: 600, missing: 1, expected: "at least 600" },
  { cached: 0, missing: 0, expected: "0" },
])("cache usage stays distinct from missing usage: $expected", ({ cached, missing, expected }) => {
  const strip = lensStripSchema.parse({
    runs: 1,
    turns: 1,
    retries: 0,
    turn_ms_p50: 1200,
    tiers: [{
      tier: 1,
      model: "test-model",
      attempts: 2,
      failed_attempts: 0,
      unmetered_attempts: 0,
      prompt_tokens: 2000,
      completion_tokens: 40,
      cached_tokens: cached,
      reasoning_tokens: null,
      unreported_cached_attempts: missing,
      unreported_reasoning_attempts: 2,
      cost_usd: 0.001,
      latency_ms_p50: 1200,
      latency_ms_p95: 1200,
      first_token_ms_p50: 1100,
      first_token_ms_p95: 1100,
    }],
  });

  render(<LensStripView strip={strip} />);

  const row = screen.getByRole("row", { name: /tier 1/ });
  const cells = within(row).getAllByRole("cell");
  expect(cells[4].textContent).toBe(expected);
  expect(cells[6].textContent).toBe("not reported");
});
