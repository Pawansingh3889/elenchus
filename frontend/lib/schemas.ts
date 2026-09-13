/**
 * Runtime shapes for the responses the lens renders numbers from.
 *
 * Everywhere else in this project invalid data fails loudly with a typed error, and a
 * cast (`as T`) asks TypeScript to believe a claim nothing checks. A backend that renamed
 * a field, or sent a string where a number was, would render a page of plausible wrong
 * figures. So these schemas are the source of truth and the types are inferred from them.
 *
 * Unknown keys are stripped, not rejected: a backend adding a field must never break a
 * deployed page, while a field that changes type or disappears must break it at once.
 * Lifted from the closed PR #65, which wrote the mechanism for exactly this kind of page.
 */

import { z } from "zod";

const count = z.number().int().nonnegative();
const optionalCount = count.nullable();

export const meSchema = z.object({
  id: z.string(),
  display_name: z.string(),
  function: z.string().nullable(),
  band: z.string().nullable(),
  may_author: z.boolean(),
  is_admin: z.boolean(),
});
export type Me = z.infer<typeof meSchema>;

export const tracedRunSchema = z.object({
  run_id: z.string(),
  survey_title: z.string(),
  started_at: z.string(),
  last_traced_at: z.string(),
  turns: count,
  decisions: count,
  retries: count,
  attempts: count,
  failed_attempts: count,
  /** Attempts that reported no tokens or no cost. Above zero, every sum is "at least". */
  unmetered_attempts: count,
  prompt_tokens: count,
  completion_tokens: count,
  cached_tokens: count,
  reasoning_tokens: count,
  /** Null when no attempt under it was priced, which is not the same as free. */
  cost_usd: z.number().nonnegative().nullable(),
  /** Summed over turns: how long respondents waited, not the sum of attempts. */
  turn_ms: count,
  first_token_ms_p50: z.number().nullable(),
});
export type TracedRun = z.infer<typeof tracedRunSchema>;

export const spanKindSchema = z.enum(["turn", "decision", "attempt", "validation"]);
export type SpanKind = z.infer<typeof spanKindSchema>;

export const spanSchema = z.object({
  id: z.string(),
  parent_id: z.string().nullable(),
  run_id: z.string().nullable(),
  kind: spanKindSchema,
  name: z.string(),
  started_at: z.string(),
  duration_ms: count,
  error: z.string().nullable(),
  prompt_version: z.string().nullable(),
  tier: z.number().int().nullable(),
  model: z.string().nullable(),
  status: z.number().int().nullable(),
  prompt_tokens: optionalCount,
  completion_tokens: optionalCount,
  cached_tokens: optionalCount,
  reasoning_tokens: optionalCount,
  first_token_ms: optionalCount,
  cost_usd: z.number().nonnegative().nullable(),
  attrs: z.record(z.string(), z.unknown()),
});
export type Span = z.infer<typeof spanSchema>;

export const tierStripSchema = z.object({
  tier: z.number().int().nullable(),
  model: z.string().nullable(),
  attempts: count,
  failed_attempts: count,
  unmetered_attempts: count,
  prompt_tokens: count,
  completion_tokens: count,
  cached_tokens: count,
  reasoning_tokens: count,
  cost_usd: z.number().nonnegative().nullable(),
  latency_ms_p50: z.number().nullable(),
  latency_ms_p95: z.number().nullable(),
  first_token_ms_p50: z.number().nullable(),
  first_token_ms_p95: z.number().nullable(),
});
export type TierStrip = z.infer<typeof tierStripSchema>;

export const lensStripSchema = z.object({
  runs: count,
  turns: count,
  retries: count,
  turn_ms_p50: z.number().nullable(),
  tiers: z.array(tierStripSchema),
});
export type LensStrip = z.infer<typeof lensStripSchema>;
