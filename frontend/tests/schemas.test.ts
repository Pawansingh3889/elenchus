/**
 * What the boundary must catch, and what it must not.
 *
 * The point of validating here is not tidiness, it is that a cast let a backend change
 * reach a results page as a plausible wrong number. Each case below is a shape the
 * server could actually send, not an imagined one.
 */

import { describe, expect, it } from "vitest";

import { dashboardRowSchema, questionReportSchema, surveyReportSchema } from "@/lib/schemas";

const question = {
  id: "q1",
  position: 1,
  text: "How cold was the chill store?",
  answer_type: "number",
  answered: 12,
  declined: 0,
  counts: [],
  selections: 12,
  average: 3.4,
  low: 2,
  high: 6,
  verbatim: [],
  follow_ups: [],
  probed: 2,
  unit: "°C",
  display_unit: null,
};

const report = {
  template_id: "t1",
  title: "Chill chain",
  runs_total: 12,
  runs_completed: 11,
  reach: 20,
  people_started: 12,
  people_completed: 11,
  questions: [question],
};

describe("the survey report boundary", () => {
  it("accepts what the server actually sends", () => {
    expect(surveyReportSchema.parse(report).questions[0]?.average).toBe(3.4);
  });

  it("rejects a number that arrived as a string", () => {
    // The failure that motivated this. JSON has numbers, but a backend that formats a
    // value for display, or a serialiser that widens a Decimal to str, sends "3.4".
    // Under the old cast this reached the page and every average computed from it was
    // string concatenation, which reads as a number and is not one.
    const result = surveyReportSchema.safeParse({
      ...report,
      questions: [{ ...question, average: "3.4" }],
    });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.path.join(".")).toBe("questions.0.average");
  });

  it("rejects a missing count rather than treating it as zero", () => {
    // `answered` is the denominator for every share on the page. Absent is not zero:
    // zero answers and an unreported field are different findings, and only one of
    // them should render.
    const withoutAnswered: Record<string, unknown> = { ...question };
    delete withoutAnswered.answered;
    const result = surveyReportSchema.safeParse({ ...report, questions: [withoutAnswered] });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.path.join(".")).toBe("questions.0.answered");
  });

  it("keeps null distinct from absent on average", () => {
    // "Null when nobody answered, not 0" is load-bearing, so null must pass and be
    // preserved rather than defaulted into a number.
    const parsed = surveyReportSchema.parse({
      ...report,
      questions: [{ ...question, average: null, low: null, high: null }],
    });
    expect(parsed.questions[0]?.average).toBeNull();
  });

  it("rejects an answer_type the app cannot render", () => {
    const result = questionReportSchema.safeParse({ ...question, answer_type: "ranking" });
    expect(result.success).toBe(false);
  });

  it("tolerates a field the backend added but this build has never heard of", () => {
    // The other half of the contract, and the reason unknown keys are stripped rather
    // than refused. A deployed frontend must survive the backend shipping first;
    // only removals and type changes are allowed to break it.
    const parsed = surveyReportSchema.parse({
      ...report,
      questions: [{ ...question, median: 3, sentiment: "warm" }],
      generated_by: "a future version",
    });
    expect(parsed.questions[0]?.average).toBe(3.4);
    expect("generated_by" in parsed).toBe(false);
  });
});

describe("the dashboard boundary", () => {
  const row = {
    id: "t1",
    title: "Chill chain",
    status: "published",
    updated_at: "2026-08-27T10:00:00Z",
    closed_at: null,
    started: 12,
    completed: 11,
    in_progress: 1,
    abandoned: 0,
    reach: 20,
    people_started: 12,
    people_completed: 11,
    last_started_at: "2026-08-27T10:00:00Z",
    last_completed_at: null,
    completion_rate: 0.91,
    response_rate: 0.55,
  };

  it("accepts a live row", () => {
    expect(dashboardRowSchema.parse(row).response_rate).toBe(0.55);
  });

  it("rejects a status this app has no rendering for", () => {
    expect(dashboardRowSchema.safeParse({ ...row, status: "paused" }).success).toBe(false);
  });

  it("allows a response rate above 1 rather than clamping it", () => {
    // An author testing their own survey answers it without being in its audience, so
    // the rate legitimately exceeds 1. Reported rather than hidden, per the field's
    // own documentation, which means the schema must not quietly bound it.
    expect(dashboardRowSchema.parse({ ...row, response_rate: 1.5 }).response_rate).toBe(1.5);
  });
});
