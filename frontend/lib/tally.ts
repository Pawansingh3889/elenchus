/**
 * One question's tally, computed from the answers rather than fetched.
 *
 * The server already reports every question, and this exists for the thing it cannot
 * do: report them over a subset. A slice ("only the people who picked Nights") has to
 * retally client-side, and the sliced and unsliced numbers must be produced by the same
 * code or the page would show two numbers of different provenance side by side and
 * invite the reader to compare them.
 *
 * So this is a faithful port of `_report_question` in backend/app/runs/service.py, and
 * the properties worth naming are the ones that took work there:
 *
 * - The author's option order, not popularity order, so a scale reads as a scale.
 * - Options nobody picked keep their row: a zero is a finding, and a missing row reads
 *   as an option that was never offered.
 * - A rating always shows all five steps, so an unused end of the scale is visible.
 * - Declines are counted apart, never as answers: a question everyone skipped and a
 *   question nobody reached are different findings.
 * - Follow-ups are listed and never counted: they answer a question the model wrote, so
 *   they belong to no option list and no scale.
 * - Write-ins are their own rows, after the author's options, and are not folded into
 *   an option that happens to read the same.
 *
 * `tests/tally.test.ts` checks it against the cases backend/tests/test_results.py pins,
 * because two implementations of one rule drift silently otherwise.
 */
import type { AnswerType, MatrixQuestion, OptionCount, QuestionReport, RunAnswer } from "./types";

export interface TallyInput {
  question: MatrixQuestion;
  /** Scripted answers to this question, one per run, declines included. */
  values: Record<string, unknown>[];
  /** Follow-up answers, printed and never counted. */
  probeValues: Record<string, unknown>[];
  /** Runs probed on this question, counted as runs so it reads against `answered`. */
  probed: number;
}

const isDecline = (value: Record<string, unknown>) => "unanswerable" in value;

export function tallyQuestion({
  question,
  values,
  probeValues,
  probed,
}: TallyInput): QuestionReport {
  const answered = values.filter((v) => !isDecline(v));
  const declined = values.length - answered.length;
  const type: AnswerType = question.answer_type;

  let counts: OptionCount[] = [];
  let verbatim: string[] = [];
  let average: number | null = null;
  let low: number | null = null;
  let high: number | null = null;

  if (type === "single_select" || type === "multi_select") {
    const tally = new Map<string, number>(question.options.map((option) => [option, 0]));
    const writeIns: string[] = [];
    for (const value of answered) {
      const chosen =
        "option" in value ? [value.option as string] : ((value.options as string[]) ?? []);
      for (const choice of chosen) {
        if (tally.has(choice)) tally.set(choice, tally.get(choice)! + 1);
      }
      const other = value.other;
      if (Array.isArray(other)) writeIns.push(...(other as string[]));
      else if (other) writeIns.push(String(other));
    }
    counts = [...tally].map(([label, count]) => ({ label, count, write_in: false }));
    // Distinct write-ins, in first-seen order, counted by how many said the same thing.
    for (const written of [...new Set(writeIns)]) {
      counts.push({
        label: written,
        count: writeIns.filter((w) => w === written).length,
        write_in: true,
      });
    }
    verbatim = writeIns;
  } else if (type === "yes_no") {
    const yes = answered.filter((v) => v.yes_no === true).length;
    counts = [
      { label: "yes", count: yes, write_in: false },
      { label: "no", count: answered.length - yes, write_in: false },
    ];
  } else if (type === "rating" || type === "number") {
    const numbers = answered
      .map((v) => v[type])
      .filter((n): n is number => typeof n === "number");
    if (numbers.length) {
      average = numbers.reduce((a, b) => a + b, 0) / numbers.length;
      low = Math.min(...numbers);
      high = Math.max(...numbers);
    }
    if (type === "rating") {
      counts = [1, 2, 3, 4, 5].map((n) => ({
        label: String(n),
        count: numbers.filter((x) => x === n).length,
        write_in: false,
      }));
    }
  } else {
    // Free text and dates: nothing to add up, so the values themselves, in full.
    verbatim = answered
      .map((v) => {
        const first = Object.values(v)[0];
        return first === undefined ? "" : String(first);
      })
      .filter(Boolean);
  }

  return {
    id: question.id,
    position: question.position,
    text: question.text,
    answer_type: type,
    answered: answered.length,
    declined,
    counts,
    // Every pick, write-ins included. Summed from `counts` rather than recounted, so a
    // sliced view and the server's report cannot disagree about the denominator. On any
    // type but multi-select this is the number of people, because one person picks once.
    selections:
      type === "single_select" || type === "multi_select"
        ? counts.reduce((n, c) => n + c.count, 0)
        : answered.length,
    average,
    low,
    high,
    verbatim,
    // A declined probe is not words the respondent said, so it is left out on the same
    // rule the tallies use. `probed` still counts the run: the question was asked, and
    // "asked and declined" is a finding.
    follow_ups: probeValues.filter((v) => !isDecline(v)).map(flattenValue),
    probed,
  };
}

/** One printable cell, matching `flatten_answer` on the server closely enough for the
 *  follow-up list, which is the only place it is used. */
function flattenValue(value: Record<string, unknown>): string {
  const first = Object.values(value)[0];
  if (Array.isArray(first)) return first.join(", ");
  return first === undefined ? "" : String(first);
}

/** Group a matrix into the per-question inputs `tallyQuestion` wants.
 *
 *  `runIds` keeps every verbatim attached to the response it came from, which is what
 *  makes a quote on this page clickable through to the person who said it. The report
 *  endpoint drops that, and it is the reason a verbatim was an anonymous string. */
export function tallyInputs(
  questions: MatrixQuestion[],
  runs: { run_id: string; answers: RunAnswer[] }[],
): Map<string, TallyInput & { runIds: string[] }> {
  const out = new Map<string, TallyInput & { runIds: string[] }>();
  for (const question of questions) {
    out.set(question.id, { question, values: [], probeValues: [], probed: 0, runIds: [] });
  }
  for (const run of runs) {
    const probedHere = new Set<string>();
    for (const answer of run.answers) {
      const input = out.get(answer.question_id);
      if (!input) continue;
      if (answer.kind === "scripted") {
        input.values.push(answer.value);
        input.runIds.push(run.run_id);
      } else {
        input.probeValues.push(answer.value);
        probedHere.add(answer.question_id);
      }
    }
    for (const questionId of probedHere) out.get(questionId)!.probed += 1;
  }
  return out;
}
