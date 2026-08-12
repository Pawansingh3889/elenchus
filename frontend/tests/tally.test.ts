import { describe, expect, test } from "vitest";

import { sliceRuns, sliceValues, parseSlice } from "@/lib/slicing";
import { tallyInputs, tallyQuestion } from "@/lib/tally";
import type { AnswersMatrix, MatrixQuestion, MatrixRun, RunAnswer } from "@/lib/types";

/**
 * The client tally against the cases the server's own tests pin.
 *
 * `lib/tally.ts` is a port of `_report_question` in backend/app/runs/service.py, and it
 * exists because a slice has to retally over a subset, which the server cannot do. Two
 * implementations of one rule drift silently, so the cases here mirror
 * backend/tests/test_results.py: the author's option order, zero rows kept, write-ins
 * counted apart, declines counted apart, the whole rating scale, and follow-ups listed
 * but never counted.
 */

const question = (over: Partial<MatrixQuestion> = {}): MatrixQuestion => ({
  id: "q1",
  position: 0,
  text: "Which aspects need improvement?",
  answer_type: "multi_select",
  options: ["Cleaning", "Waste", "PPE"],
  ...over,
});

const scripted = (value: Record<string, unknown>, questionId = "q1"): RunAnswer => ({
  question_id: questionId,
  kind: "scripted",
  question_text: "Which aspects need improvement?",
  value,
  answered_at: "2026-08-12T00:00:00Z",
});

const run = (id: string, answers: RunAnswer[]): MatrixRun => ({
  run_id: id,
  respondent_label: `Respondent ${id}`,
  status: "completed",
  started_at: "2026-08-12T00:00:00Z",
  completed_at: "2026-08-12T00:10:00Z",
  answers,
});

describe("the tally matches what the server reports", () => {
  test("keeps the author's option order and every zero row", () => {
    const report = tallyQuestion({
      question: question(),
      values: [{ options: ["Cleaning", "Waste"] }, { options: ["Cleaning"] }],
      probeValues: [],
      probed: 0,
    });

    // A zero is a finding; a missing row reads as an option nobody was offered.
    expect(report.counts.map((c) => [c.label, c.count])).toEqual([
      ["Cleaning", 2],
      ["Waste", 1],
      ["PPE", 0],
    ]);
  });

  test("counts a write-in as its own row rather than folding it into an option", () => {
    const report = tallyQuestion({
      question: question(),
      values: [{ options: ["Cleaning"], other: ["drains blocked again"] }],
      probeValues: [],
      probed: 0,
    });

    const writeIns = report.counts.filter((c) => c.write_in);
    expect(writeIns.map((c) => [c.label, c.count])).toEqual([["drains blocked again", 1]]);
    expect(report.verbatim).toEqual(["drains blocked again"]);
  });

  test("a write-in reading the same as an option stays a separate row", () => {
    // The distinction the server is most careful about: counting is where it matters.
    const report = tallyQuestion({
      question: question(),
      values: [{ options: ["Cleaning"] }, { options: [], other: ["Cleaning"] }],
      probeValues: [],
      probed: 0,
    });

    expect(report.counts.filter((c) => !c.write_in).find((c) => c.label === "Cleaning")?.count).toBe(1);
    expect(report.counts.filter((c) => c.write_in).find((c) => c.label === "Cleaning")?.count).toBe(1);
  });

  test("counts declines apart from answers", () => {
    const report = tallyQuestion({
      question: question(),
      values: [{ options: ["PPE"] }, { unanswerable: "would rather not say" }],
      probeValues: [],
      probed: 0,
    });

    expect(report.answered).toBe(1);
    expect(report.declined).toBe(1);
  });

  test("a rating shows the whole scale and its spread", () => {
    const report = tallyQuestion({
      question: question({ answer_type: "rating", options: [] }),
      values: [{ rating: 4 }, { rating: 2 }],
      probeValues: [],
      probed: 0,
    });

    expect(report.counts.map((c) => c.label)).toEqual(["1", "2", "3", "4", "5"]);
    expect(report.average).toBe(3);
    expect([report.low, report.high]).toEqual([2, 4]);
  });

  test("yes and no both get a row even when nobody said one of them", () => {
    const report = tallyQuestion({
      question: question({ answer_type: "yes_no", options: [] }),
      values: [{ yes_no: true }, { yes_no: true }],
      probeValues: [],
      probed: 0,
    });

    expect(report.counts.map((c) => [c.label, c.count])).toEqual([
      ["yes", 2],
      ["no", 0],
    ]);
  });

  test("follow-ups are listed and never counted", () => {
    const report = tallyQuestion({
      question: question({ answer_type: "short_text", options: [] }),
      values: [{ text: "the guillotine" }],
      probeValues: [{ text: "every other week" }, { unanswerable: "not sure" }],
      probed: 1,
    });

    expect(report.answered).toBe(1);
    expect(report.probed).toBe(1);
    // A declined probe is not words the respondent said, so it is left out.
    expect(report.follow_ups).toEqual(["every other week"]);
  });

  test("a rating with no answers has no average rather than an average of zero", () => {
    const report = tallyQuestion({
      question: question({ answer_type: "rating", options: [] }),
      values: [{ unanswerable: "skipped" }],
      probeValues: [],
      probed: 0,
    });

    // Null, not 0: zero would read as everyone scoring the bottom of the scale.
    expect(report.average).toBeNull();
    expect(report.counts.every((c) => c.count === 0)).toBe(true);
  });
});

describe("grouping a matrix keeps each answer with its response", () => {
  test("a verbatim can be traced back to the run it came from", () => {
    const inputs = tallyInputs(
      [question({ answer_type: "short_text", options: [] })],
      [run("r1", [scripted({ text: "the guillotine" })]), run("r2", [scripted({ text: "the press" })])],
    );

    // The thing the report endpoint cannot do: a verbatim on the page is clickable
    // through to the person who said it, because the run id travelled with it.
    expect(inputs.get("q1")!.runIds).toEqual(["r1", "r2"]);
  });

  test("one run probed twice on a question counts as one probed run", () => {
    const probe = (text: string): RunAnswer => ({
      question_id: "q1",
      kind: "follow_up",
      question_text: "Which line?",
      value: { text },
      answered_at: "2026-08-12T00:00:00Z",
    });
    const inputs = tallyInputs(
      [question({ answer_type: "short_text", options: [] })],
      [run("r1", [scripted({ text: "a lead" }), probe("trim"), probe("nights")])],
    );

    // `probed` counts runs, not probes, so it reads against `answered` on one scale.
    expect(inputs.get("q1")!.probed).toBe(1);
    expect(inputs.get("q1")!.probeValues).toHaveLength(2);
  });
});

describe("slicing", () => {
  const shift = question({ id: "q2", answer_type: "single_select", options: ["Days", "Nights"] });
  const runs = [
    run("r1", [scripted({ option: "Nights" }, "q2"), scripted({ rating: 2 }, "q3")]),
    run("r2", [scripted({ option: "Days" }, "q2"), scripted({ rating: 5 }, "q3")]),
    run("r3", [scripted({ option: "Nights" }, "q2"), scripted({ rating: 1 }, "q3")]),
  ];

  test("keeps only the runs that gave that answer", () => {
    const nights = sliceRuns(runs, { questionId: "q2", value: "Nights" });
    expect(nights.map((r) => r.run_id)).toEqual(["r1", "r3"]);
  });

  test("retallying the sliced runs answers the cross-question question", () => {
    // The whole point: the people who work Nights rate this worse than everyone does.
    const nights = sliceRuns(runs, { questionId: "q2", value: "Nights" });
    const sliced = tallyInputs([question({ id: "q3", answer_type: "rating", options: [] })], nights);
    const all = tallyInputs([question({ id: "q3", answer_type: "rating", options: [] })], runs);

    expect(tallyQuestion(sliced.get("q3")!).average).toBe(1.5);
    expect(tallyQuestion(all.get("q3")!).average).toBeCloseTo(2.667, 2);
  });

  test("offers every option the author wrote, including one nobody picked", () => {
    // From the definition, not the data: an empty group is a finding, and slicing on
    // what happens to appear would hide it.
    expect(sliceValues(shift)).toEqual(["Days", "Nights"]);
    expect(sliceRuns(runs, { questionId: "q2", value: "Days" })).toHaveLength(1);
  });

  test("a write-in cannot be sliced on", () => {
    const withWriteIn = [run("r4", [scripted({ options: [], other: ["Twilight"] }, "q2")])];
    expect(sliceRuns(withWriteIn, { questionId: "q2", value: "Twilight" })).toEqual([]);
  });

  test("a slice naming a question this survey does not have reads as no slice", () => {
    const matrix = { questions: [shift] } as AnswersMatrix;
    expect(parseSlice("q9:Days", matrix)).toBeNull();
    expect(parseSlice("q2:Days", matrix)).toEqual({ questionId: "q2", value: "Days" });
  });
});
