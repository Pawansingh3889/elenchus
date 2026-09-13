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
  template_id: z.string(),
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

/** One call to one tier, placed in its run and turn: the Inference page's unit. */
export const attemptRowSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  survey_title: z.string(),
  started_at: z.string(),
  turn_number: count,
  question_index: optionalCount,
  /** The ask this attempt served was a nudged retry after a refusal. */
  retry: z.boolean(),
  transcript_messages: optionalCount,
  tier: z.number().int().nullable(),
  model: z.string().nullable(),
  status: z.number().int().nullable(),
  error: z.string().nullable(),
  duration_ms: count,
  first_token_ms: optionalCount,
  prompt_tokens: optionalCount,
  cached_tokens: optionalCount,
  completion_tokens: optionalCount,
  reasoning_tokens: optionalCount,
  cost_usd: z.number().nonnegative().nullable(),
});
export type AttemptRow = z.infer<typeof attemptRowSchema>;

/**
 * One ask of the model: what the engine knew, what it offered, what the model picked,
 * what the check concluded, and what the ask's own calls cost. State fields are null on
 * asks traced before they were recorded, which is unknown, not false.
 */
export const decisionRowSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  survey_title: z.string(),
  started_at: z.string(),
  turn_number: count,
  question_index: optionalCount,
  retry: z.boolean(),
  duration_ms: count,
  error: z.string().nullable(),
  answer_type: z.string().nullable(),
  follow_up_policy: z.string().nullable(),
  forced_probe: z.boolean().nullable(),
  probe_outstanding: z.boolean().nullable(),
  scripted_recorded: z.boolean().nullable(),
  recorded_this_turn: z.boolean().nullable(),
  follow_ups_used: optionalCount,
  replies_used: optionalCount,
  transcript_messages: optionalCount,
  tools_offered: z.array(z.string()),
  resolved_to: z.string().nullable(),
  picked: z.string().nullable(),
  outcome: z.string().nullable(),
  reason: z.string().nullable(),
  attempts: count,
  failed_attempts: count,
  attempt_ms: count,
  cost_usd: z.number().nonnegative().nullable(),
});
export type DecisionRow = z.infer<typeof decisionRowSchema>;

export const correlationCellSchema = z.object({
  factor: z.string(),
  outcome: z.string(),
  n: count,
  rho: z.number().min(-1).max(1).nullable(),
  ci_low: z.number().min(-1).max(1).nullable(),
  ci_high: z.number().min(-1).max(1).nullable(),
  /** Below the minimum sample: shown for reference, never ranked or coloured. */
  too_few: z.boolean(),
  /** rho is null because one side never varied across these calls. */
  no_variation: z.boolean(),
});
export type CorrelationCell = z.infer<typeof correlationCellSchema>;

export const correlationMatrixSchema = z.object({
  factors: z.array(z.string()),
  outcomes: z.array(z.string()),
  min_samples: count,
  cells: z.array(correlationCellSchema),
});
export type CorrelationMatrix = z.infer<typeof correlationMatrixSchema>;

/** What building one embedding report spent, measured from the ledger. A repeat view reads
 *  the cache, so $0 with every text cached is the cache working, not a missing figure. */
export const embeddingCostSchema = z.object({
  texts: count,
  cached: count,
  embedded: count,
  calls: count,
  prompt_tokens: count,
  cost_usd: z.number().nonnegative(),
  /** Calls that reported no usage: the cost is then a floor. */
  unmetered_calls: count,
  duration_ms: count,
});
export type EmbeddingCost = z.infer<typeof embeddingCostSchema>;

export const mapPointSchema = z.object({
  answer_id: z.string(),
  run_id: z.string(),
  kind: z.string(),
  recorded: z.string(),
  said: z.string(),
  x: z.number(),
  y: z.number(),
  neighbours: z.array(z.string()),
});
export type MapPoint = z.infer<typeof mapPointSchema>;

export const mapQuestionSchema = z.object({
  position: count,
  text: z.string(),
  answer_type: z.string(),
  points: z.array(mapPointSchema),
});
export type MapQuestion = z.infer<typeof mapQuestionSchema>;

export const answerMapSchema = z.object({
  survey_title: z.string(),
  model: z.string(),
  unplaced: count,
  questions: z.array(mapQuestionSchema),
  cost: embeddingCostSchema,
});
export type AnswerMap = z.infer<typeof answerMapSchema>;

export const themeSchema = z.object({
  size: count,
  runs: count,
  representative: z.string(),
  members: z.array(z.string()),
});

export const themeQuestionSchema = z.object({
  position: count,
  text: z.string(),
  texts: count,
  themes: z.array(themeSchema),
});
export type ThemeQuestion = z.infer<typeof themeQuestionSchema>;

export const themeReportSchema = z.object({
  survey_title: z.string(),
  model: z.string(),
  questions: z.array(themeQuestionSchema),
  cost: embeddingCostSchema,
});
export type ThemeReport = z.infer<typeof themeReportSchema>;

export const duplicatePairSchema = z.object({
  first: z.string(),
  second: z.string(),
  first_run: z.string(),
  second_run: z.string(),
  similarity: z.number(),
});

export const duplicateReportSchema = z.object({
  survey_title: z.string(),
  model: z.string(),
  threshold: z.number(),
  texts: count,
  pairs: z.array(duplicatePairSchema),
  cost: embeddingCostSchema,
});
export type DuplicateReport = z.infer<typeof duplicateReportSchema>;

export const groundingJudgedSchema = z.object({
  said: z.string(),
  option: z.string(),
  options: z.array(z.string()),
  language: z.string(),
  supported: z.boolean(),
  word_supported: z.boolean(),
  similarity: z.number(),
  /** The chosen option's similarity less the best other option's. */
  margin: z.number(),
});
export type GroundingJudged = z.infer<typeof groundingJudgedSchema>;

export const groundingReportSchema = z.object({
  measured_at: z.string(),
  model: z.string(),
  pairs: count,
  negatives: count,
  word_false_accepts: count,
  word_false_refusals: count,
  recommended_margin: z.number().nullable(),
  at_recommended_false_accepts: count.nullable(),
  at_recommended_false_refusals: count.nullable(),
  highest_negative_margin: z.number().nullable(),
  lowest_positive_margin: z.number().nullable(),
  sweep: z.array(z.object({ margin: z.number(), false_accepts: count, false_refusals: count })),
  judged: z.array(groundingJudgedSchema),
  semantic_enabled: z.boolean(),
  configured_margin: z.number().nullable(),
});
export type GroundingReport = z.infer<typeof groundingReportSchema>;

/* The interpretability lens: a local model (Qwen3-0.6B) reading the exact prompt a hosted
 * model was sent. Nothing here is the hosted model's internals. Probabilities are left
 * unbounded above: a softmax summed in floating point can land a hair past 1. */

export const interpStatusSchema = z.object({
  enabled: z.boolean(),
  reachable: z.boolean(),
  model: z.string().nullable(),
  revision: z.string().nullable(),
  device: z.string().nullable(),
  /** Why it is not reachable, in words, when it is not. */
  detail: z.string().nullable(),
});
export type InterpStatus = z.infer<typeof interpStatusSchema>;

export const capturedAskSchema = z.object({
  span_id: z.string(),
  run_id: z.string(),
  survey_title: z.string(),
  started_at: z.string(),
  hosted_model: z.string().nullable(),
  tools_offered: z.array(z.string()),
  hosted_pick: z.string().nullable(),
  outcome: z.string().nullable(),
  hosted_ms: count,
  hosted_prompt_tokens: count.nullable(),
  hosted_cost_usd: z.number().nonnegative().nullable(),
  analysed: z.boolean(),
  attributed: z.boolean(),
  qwen_pick: z.string().nullable(),
  qwen_probability_of_hosted_pick: z.number().nonnegative().nullable(),
  agrees: z.boolean().nullable(),
  analysis_ms: count.nullable(),
  analysis_cost_usd: z.number().nonnegative().nullable(),
  attribution_ms: count.nullable(),
  attribution_cost_usd: z.number().nonnegative().nullable(),
});
export type CapturedAsk = z.infer<typeof capturedAskSchema>;

const promptSectionSchema = z.object({
  key: z.string(),
  label: z.string(),
  kind: z.enum(["system", "tools", "message", "template"]),
  role: z.string().nullable(),
  tokens: count,
});
export type PromptSection = z.infer<typeof promptSectionSchema>;

const tokenWeightSchema = z.object({
  position: count,
  text: z.string(),
  section: z.string(),
  weight: z.number(),
});
export type TokenWeight = z.infer<typeof tokenWeightSchema>;

export const analysisSchema = z.object({
  model: z.string(),
  revision: z.string(),
  device: z.string(),
  dtype: z.string(),
  prompt_tokens: count,
  sections: z.array(promptSectionSchema),
  calls_a_tool: z.number().nonnegative(),
  tools: z.array(
    z.object({ name: z.string(), logprob: z.number(), probability: z.number().nonnegative() }),
  ),
  pick: z.string(),
  layers: z.array(
    z.object({
      layer: count,
      norm: z.number().nonnegative(),
      tool_probabilities: z.record(z.string(), z.number()),
      top_token: z.string(),
    }),
  ),
  attention: z.array(z.object({ layer: count, shares: z.record(z.string(), z.number()) })),
  attended_tokens: z.array(tokenWeightSchema),
  timings: z.object({ render_ms: count, read_ms: count, tools_ms: count, total_ms: count }),
});
export type Analysis = z.infer<typeof analysisSchema>;

export const attributionResultSchema = z.object({
  model: z.string(),
  revision: z.string(),
  device: z.string(),
  prompt_tokens: count,
  attribution: z.object({
    /** The tool the hosted model called: the choice this explains. */
    target: z.string(),
    /** Shares of the total absolute attribution; positive plus negative over all adds to 1. */
    sections: z.record(z.string(), z.object({ positive: z.number(), negative: z.number() })),
    tokens: z.array(tokenWeightSchema),
    respondent_words: z.array(z.object({ text: z.string(), score: z.number() })),
  }),
  render_ms: count,
  attribution_ms: count,
  total_ms: count,
});
export type AttributionResult = z.infer<typeof attributionResultSchema>;

export const storedAnalysisSchema = z.object({
  span_id: z.string(),
  run_id: z.string().nullable(),
  target_tool: z.string().nullable(),
  analysed_at: z.string(),
  duration_ms: count,
  cost_usd: z.number().nonnegative().nullable(),
  hosted_model: z.string().nullable(),
  hosted_ms: count,
  hosted_cost_usd: z.number().nonnegative().nullable(),
  analysis: analysisSchema,
  /** Asked for separately: it takes several times as long as the reading. */
  attribution: z
    .object({
      attributed_at: z.string(),
      duration_ms: count,
      cost_usd: z.number().nonnegative().nullable(),
      result: attributionResultSchema,
    })
    .nullable(),
});
export type StoredAnalysis = z.infer<typeof storedAnalysisSchema>;

export const promptVersionSchema = z.object({
  name: z.string(),
  source: z.enum(["file", "database"]),
  active: z.boolean(),
  created_at: z.string().nullable(),
  created_by_name: z.string().nullable(),
  note: z.string().nullable(),
  /** From the trace; null means no traced turn ran on it, not that it never ran. */
  turns: optionalCount,
  runs: optionalCount,
  turn_ms_p50: z.number().nullable(),
  cost_usd: z.number().nonnegative().nullable(),
});
export type PromptVersion = z.infer<typeof promptVersionSchema>;

export const promptFamilySchema = z.object({
  family: z.string(),
  active: z.string(),
  default: z.string(),
  versions: z.array(promptVersionSchema),
});
export type PromptFamily = z.infer<typeof promptFamilySchema>;

export const promptBodySchema = z.object({
  name: z.string(),
  source: z.enum(["file", "database"]),
  body: z.string(),
});
export type PromptBody = z.infer<typeof promptBodySchema>;

/* The evaluation lens: people's labels on recorded answers, and a judge scored against
 * them. A label is the truth here; the judge's verdict is an opinion shown beside it. */

export const labelVerdictSchema = z.enum(["supported", "invented", "unsure"]);
export type LabelVerdict = z.infer<typeof labelVerdictSchema>;

export const evalItemSchema = z.object({
  /** "corpus:<fixture>:<index>" or "answer:<uuid>". */
  key: z.string(),
  source: z.enum(["corpus", "runs"]),
  origin: z.string(),
  run_id: z.string().nullable(),
  model: z.string().nullable(),
  when: z.string().nullable(),
  question_text: z.string(),
  answer_type: z.string(),
  options: z.array(z.string()),
  kind: z.string(),
  value: z.record(z.string(), z.unknown()),
  said: z.array(z.string()),
  judge_supported: z.boolean().nullable(),
  judge_why: z.string().nullable(),
  judge_prompt: z.string().nullable(),
  marked_invented: z.boolean(),
  label: labelVerdictSchema.nullable(),
  note: z.string().nullable(),
  labelled_at: z.string().nullable(),
});
export type EvalItem = z.infer<typeof evalItemSchema>;

export const rateSchema = z.object({
  numerator: count,
  denominator: count,
  value: z.number().nonnegative().nullable(),
  low: z.number().nonnegative().nullable(),
  high: z.number().nonnegative().nullable(),
  /** Below the minimum labelled: shown for reference, never read as a finding. */
  too_few: z.boolean(),
});
export type Rate = z.infer<typeof rateSchema>;

export const faithfulnessSliceSchema = z.object({
  name: z.string(),
  items: count,
  labelled: count,
  supported: count,
  invented: count,
  unsure: count,
  invention_rate: rateSchema,
  judged_and_labelled: count,
  judge_precision: rateSchema,
  judge_recall: rateSchema,
  judge_false_alarms: rateSchema,
});
export type FaithfulnessSlice = z.infer<typeof faithfulnessSliceSchema>;

export const faithfulnessReportSchema = z.object({
  min_labelled: count,
  overall: faithfulnessSliceSchema,
  by_source: z.array(faithfulnessSliceSchema),
  by_answer_type: z.array(faithfulnessSliceSchema),
  by_model: z.array(faithfulnessSliceSchema),
});
export type FaithfulnessReport = z.infer<typeof faithfulnessReportSchema>;

export const judgeRunSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  prompt_version: z.string(),
  model: z.string().nullable(),
  tier: z.number().int().nullable(),
  answers: count,
  flagged: count,
  cost_usd: z.number().nonnegative(),
  /** Calls that reported no usage: the cost is then a floor. */
  unmetered_calls: count,
  duration_ms: count,
  judged_at: z.string(),
});
export type JudgeRun = z.infer<typeof judgeRunSchema>;

export const medianSchema = z.object({
  value: z.number().nullable(),
  /** How many measurements the median is over. */
  n: count,
});
export type Median = z.infer<typeof medianSchema>;

export const qualitySliceSchema = z.object({
  name: z.string(),
  runs: count,
  completion: rateSchema,
  answers: count,
  declined: rateSchema,
  turns_per_answer: medianSchema,
  respondent_chars: medianSchema,
  minutes_to_complete: medianSchema,
  wait_ms_per_turn: medianSchema,
  follow_ups_asked: count,
  follow_up_answers: count,
  follow_up_new_words: medianSchema,
  cost_per_completed_run: medianSchema,
  cost_per_answer: z.number().nonnegative().nullable(),
  unmetered_calls: count,
});
export type QualitySlice = z.infer<typeof qualitySliceSchema>;

export const qualityReportSchema = z.object({
  runs_without_conversation: count,
  overall: qualitySliceSchema,
  by_survey: z.array(qualitySliceSchema),
  by_model: z.array(qualitySliceSchema),
  by_prompt: z.array(qualitySliceSchema),
});
export type QualityReport = z.infer<typeof qualityReportSchema>;

/* Evaluation runs: scripted scenarios through the real engine, pinned and capped. */

export const evalOptionsSchema = z.object({
  scenarios: z.array(
    z.object({ key: z.string(), title: z.string(), questions: count, max_turns: count }),
  ),
  tiers: z.array(z.object({ tier: z.number().int(), model: z.string() })),
  prompt_versions: z.array(z.string()),
  active_prompt: z.string(),
});
export type EvalOptions = z.infer<typeof evalOptionsSchema>;

export const evalRunStatusSchema = z.enum(["queued", "running", "completed", "capped", "failed"]);

export const evalRunSchema = z.object({
  id: z.string(),
  batch_id: z.string(),
  position: count,
  scenario: z.string(),
  tier: z.number().int(),
  model: z.string().nullable(),
  prompt_version: z.string(),
  status: evalRunStatusSchema,
  cap_usd: z.number().nonnegative(),
  run_id: z.string().nullable(),
  template_id: z.string().nullable(),
  turns: count,
  answers: count,
  hard_failures: count,
  soft_failures: count,
  checks: z.array(
    z.object({ name: z.string(), ok: z.boolean(), hard: z.boolean(), detail: z.unknown() }),
  ),
  cost_usd: z.number().nonnegative(),
  unmetered_calls: count,
  duration_ms: count,
  error: z.string().nullable(),
  queued_at: z.string(),
  started_at: z.string().nullable(),
  finished_at: z.string().nullable(),
  heartbeat_at: z.string().nullable(),
  /** Running, but not heard from in a while: its process has probably gone. */
  stale: z.boolean(),
});
export type EvalRun = z.infer<typeof evalRunSchema>;
