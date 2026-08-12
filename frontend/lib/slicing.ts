/**
 * Reading the results over a subset of the people who answered.
 *
 * "Did the people who said X also say Y" is the question a survey is run to answer, and
 * it is the one this app could not ask: the report tallies each question alone, and the
 * respondent view showed one person at a time. A slice is the join, done in the client
 * over the answers matrix.
 *
 * Only closed answers can be sliced on. Free text cannot: two people describing the same
 * thing in different words are not the same group, and pretending otherwise would build
 * a filter that silently drops half of who it claims to include.
 */
import type { AnswersMatrix, MatrixQuestion, MatrixRun } from "./types";

/**
 * The smallest group a slice will show.
 *
 * Zero, deliberately, and this is where a threshold would go. `docs/ACCESS_AND_RESULTS.md`
 * records the decision: "Results will be sliceable by any closed answer, so a filtered
 * total over a group of two is in effect those two people's answers. This was declined
 * knowingly. The slicing should be built so a threshold is one constant away."
 *
 * This is that constant. Raising it to 3 is the entire implementation, because every
 * sliced view goes through `sliceRuns` below.
 */
export const SLICE_MIN_GROUP = 0;

/** A chosen slice: one question, one of its values. */
export interface Slice {
  questionId: string;
  value: string;
}

export const SLICEABLE_TYPES = ["single_select", "multi_select", "yes_no", "rating"] as const;

export function sliceableQuestions(questions: MatrixQuestion[]): MatrixQuestion[] {
  return questions.filter((q) =>
    (SLICEABLE_TYPES as readonly string[]).includes(q.answer_type),
  );
}

/** The values a question can be sliced by, in the author's own order.
 *
 *  From the question definition rather than from the data, so an option nobody picked is
 *  offered and comes back empty, which is a finding. Slicing on what happens to appear
 *  would hide exactly that. */
export function sliceValues(question: MatrixQuestion): string[] {
  if (question.answer_type === "yes_no") return ["yes", "no"];
  if (question.answer_type === "rating") return ["1", "2", "3", "4", "5"];
  return question.options;
}

/** Whether one answer value counts as the slice's value.
 *
 *  Matched against the stored shape rather than a printed string, so an option and a
 *  write-in that read the same do not collapse into one group. A write-in is not an
 *  option and cannot be sliced on: it is one person's words, and a group of one is not
 *  a group. */
function matches(value: Record<string, unknown>, wanted: string): boolean {
  if ("unanswerable" in value) return false;
  if ("option" in value) return value.option === wanted;
  if ("options" in value) return (value.options as string[]).includes(wanted);
  if ("yes_no" in value) return (value.yes_no ? "yes" : "no") === wanted;
  if ("rating" in value) return String(value.rating) === wanted;
  return false;
}

/**
 * The runs that answered `slice.questionId` with `slice.value`.
 *
 * Returns every run when there is no slice. Returns nothing when the group is smaller
 * than `SLICE_MIN_GROUP`, which is the single point a suppression threshold would act
 * at; at 0 that branch never fires.
 */
export function sliceRuns(runs: MatrixRun[], slice: Slice | null): MatrixRun[] {
  if (!slice) return runs;
  const inGroup = runs.filter((run) =>
    run.answers.some(
      (a) => a.kind === "scripted" && a.question_id === slice.questionId && matches(a.value, slice.value),
    ),
  );
  return inGroup.length < SLICE_MIN_GROUP ? [] : inGroup;
}

/** Parse `?slice=<questionId>:<value>`. Returns null for anything that does not name a
 *  question this survey has, so a stale or hand-edited URL reads as no slice rather than
 *  as an empty result the author cannot explain. */
export function parseSlice(raw: string | null, matrix: AnswersMatrix | undefined): Slice | null {
  if (!raw || !matrix) return null;
  const at = raw.indexOf(":");
  if (at < 1) return null;
  const questionId = raw.slice(0, at);
  const value = raw.slice(at + 1);
  if (!value) return null;
  return matrix.questions.some((q) => q.id === questionId) ? { questionId, value } : null;
}

export const formatSlice = (slice: Slice) => `${slice.questionId}:${slice.value}`;
