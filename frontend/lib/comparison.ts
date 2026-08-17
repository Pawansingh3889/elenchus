import type { MatrixQuestion, MatrixRun } from "./types";

/**
 * Splitting the people who answered into groups, so a chart can compare them.
 *
 * This is what earns colour on the report. A tally of options is one series, where a
 * hue per bar would claim the options differ in kind when they differ only in count;
 * grouping by how people answered another question is a real second dimension, and the
 * colours then identify something a reader can act on: packing said one thing, filleting
 * said another.
 */

/** Four, because the series palette is four. */
export const MAX_GROUPS = 4;

export interface Group {
  label: string;
  runs: MatrixRun[];
}

/** The answer this run gave to the grouping question, as one printable label. */
function answerOf(run: MatrixRun, question: MatrixQuestion): string | null {
  // Scripted only: a follow-up answers a question the model wrote, so it belongs to no
  // option list and cannot name a group.
  const answer = run.answers.find((a) => a.question_id === question.id && a.kind === "scripted");
  const value = answer?.value;
  if (!value) return null;
  if ("option" in value) return String(value.option);
  if ("yes_no" in value) return value.yes_no ? "yes" : "no";
  if ("rating" in value) return String(value.rating);
  // Multi-select, free text and dates are deliberately absent. A person who ticked three
  // options belongs to three groups at once, and grouping on prose would make one group
  // per respondent: both produce a chart that cannot be read.
  return null;
}

/**
 * Runs grouped by their answer, largest group first, capped at four plus "other".
 *
 * Largest first so the colours land on the groups carrying the most people, and the cap
 * is a fold rather than a truncation: a fifth group joins "other" and is still counted,
 * because a chart that silently drops people is worse than one that says "other".
 *
 * People who did not answer the grouping question are left out entirely rather than
 * folded in. "Did not say which area" is not an area, and putting them in a bar beside
 * packing and filleting would invent a group nobody belongs to.
 */
export function groupRuns(runs: MatrixRun[], question: MatrixQuestion): Group[] {
  const byLabel = new Map<string, MatrixRun[]>();
  for (const run of runs) {
    const label = answerOf(run, question);
    if (label === null) continue;
    byLabel.set(label, [...(byLabel.get(label) ?? []), run]);
  }
  const sorted = [...byLabel.entries()].sort((a, b) => b[1].length - a[1].length);
  const kept = sorted.slice(0, MAX_GROUPS).map(([label, group]) => ({ label, runs: group }));
  const rest = sorted.slice(MAX_GROUPS).flatMap(([, group]) => group);
  return rest.length > 0 ? [...kept, { label: "other", runs: rest }] : kept;
}

/**
 * The colour for a series, by position and never by rank within a chart.
 *
 * Position in the group list, so a filter that removes one group does not repaint the
 * survivors: colour follows the entity, and a legend a reader has learned must keep
 * meaning what it meant a moment ago.
 */
export function seriesColour(index: number, label: string): string {
  if (label === "other") return "var(--series-other)";
  return `var(--series-${Math.min(index + 1, MAX_GROUPS)})`;
}
