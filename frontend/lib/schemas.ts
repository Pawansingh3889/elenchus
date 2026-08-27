/**
 * Runtime shapes for the responses this app renders numbers from.
 *
 * Everywhere else in this project, invalid data fails loudly with a typed error. The
 * frontend was the exception: `request<T>` ended in `(await res.json()) as T`, a cast
 * that asks TypeScript to believe a claim nothing checks. A backend that renamed a
 * field, or started sending a string where a number was, compiled clean and rendered a
 * results page full of plausible wrong figures. `average` becoming null-as-string, or
 * `answered` arriving as `"12"`, both survive a cast and both poison an average.
 *
 * So these schemas are the source of truth and the TypeScript types are inferred from
 * them, rather than the two being written twice and drifting. The doc comments moved
 * here with the fields they describe.
 *
 * **Unknown keys are stripped, not rejected**, which is zod's default and the right
 * semantics here: the backend adding a field must never break a deployed frontend,
 * while a field that changes type or disappears must break it immediately. Additive
 * changes stay safe; the changes that actually corrupt a page are the ones that fail.
 *
 * Scope is deliberate. This covers the survey report and the dashboard, which is where
 * the numbers are and where a silent wrong value does real damage. The remaining
 * responses are still cast, and moving them here is mechanical.
 */

import { z } from "zod";

export const answerTypeSchema = z.enum([
  "single_select",
  "multi_select",
  "yes_no",
  "short_text",
  "long_text",
  "rating",
  "number",
  "date",
]);

export const templateStatusSchema = z.enum(["draft", "published", "closed", "archived"]);

export const optionCountSchema = z.object({
  label: z.string(),
  count: z.number(),
  write_in: z.boolean(),
});

export const questionReportSchema = z.object({
  id: z.string(),
  position: z.number(),
  text: z.string(),
  answer_type: answerTypeSchema,
  answered: z.number(),
  declined: z.number(),
  counts: z.array(optionCountSchema),
  /** Every pick, across everyone who answered. Equals `answered` on every type where one
   *  person makes one choice, and does not on a multi-select: three people picking two
   *  options each is six selections from three people. `answered` is the denominator for
   *  "what share of people said this", `selections` for "what share of the picks". */
  selections: z.number(),
  /** Ratings and numbers only. Null when nobody answered, not 0. The distinction is the
   *  reason this is `.nullable()` rather than defaulted: a zero average and no answers
   *  at all are different findings, and a default would quietly merge them. */
  average: z.number().nullable(),
  /** The spread, for the same two types. An average alone hides whether everyone said
   *  twenty or half said five and half said forty. */
  low: z.number().nullable(),
  high: z.number().nullable(),
  /** Free text and write-ins, verbatim and in full. Counted on the page, shown on click. */
  verbatim: z.array(z.string()),
  /** What the probes drew out. Never in `counts` or `average`: a follow-up answers a
   *  question the model wrote, so it belongs to no option list and no scale. */
  follow_ups: z.array(z.string()),
  /** Runs probed on this question, not probes asked, so it reads against `answered`. */
  probed: z.number(),
  /** The unit the numbers are in, and an optional second unit also shown. */
  unit: z.string().nullish(),
  display_unit: z.string().nullish(),
});

export const surveyReportSchema = z.object({
  template_id: z.string(),
  title: z.string(),
  runs_total: z.number(),
  runs_completed: z.number(),
  reach: z.number(),
  people_started: z.number(),
  people_completed: z.number(),
  questions: z.array(questionReportSchema),
});

export const dashboardRowSchema = z.object({
  id: z.string(),
  title: z.string(),
  status: templateStatusSchema,
  updated_at: z.string(),
  closed_at: z.string().nullable(),
  started: z.number(),
  completed: z.number(),
  in_progress: z.number(),
  abandoned: z.number(),
  /** People rather than runs: how many this survey is for, and how many of them have
   *  opened and finished it. Kept beside the run counts rather than replacing them,
   *  because "how is this going" and "how many of the people it was for have answered"
   *  are different questions. */
  reach: z.number(),
  people_started: z.number(),
  people_completed: z.number(),
  last_started_at: z.string().nullable(),
  last_completed_at: z.string().nullable(),
  completion_rate: z.number().nullable(),
  /** Of the people this survey is for, how many finished. Null when it is aimed at
   *  nobody. Can exceed 1: an author testing their own survey answers it without being
   *  in its audience, which is reported rather than hidden. */
  response_rate: z.number().nullable(),
});

export const dashboardSchema = z.array(dashboardRowSchema);

export type AnswerType = z.infer<typeof answerTypeSchema>;
export type TemplateStatus = z.infer<typeof templateStatusSchema>;
export type OptionCount = z.infer<typeof optionCountSchema>;
export type QuestionReport = z.infer<typeof questionReportSchema>;
export type SurveyReport = z.infer<typeof surveyReportSchema>;
export type DashboardRow = z.infer<typeof dashboardRowSchema>;
