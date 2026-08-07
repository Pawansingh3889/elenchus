import type { QuestionInput } from "./types";

/**
 * Repoint visibility conditions after questions have been reordered or deleted.
 *
 * Conditions reference a question by **position**, so any edit that shifts positions
 * silently retargets them — a condition meaning "only if they said Quality Manager"
 * quietly becomes a condition on whatever question landed in that slot. The backend
 * cannot detect this; the only place that knows a move happened is here.
 *
 * `orderOfOldIndexes[newIndex] = oldIndex`, so a delete is simply that index missing.
 * A condition is cleared rather than guessed at when its target was deleted, or when
 * the move left it pointing forwards — the server refuses a forward reference, so
 * keeping one would make the draft unsaveable.
 */
export function remapConditions(
  reordered: QuestionInput[],
  orderOfOldIndexes: number[],
): QuestionInput[] {
  const newIndexOf = new Map<number, number>();
  orderOfOldIndexes.forEach((oldIndex, newIndex) => newIndexOf.set(oldIndex, newIndex));

  return reordered.map((question, newIndex) => {
    if (!question.show_when) return question;
    const target = newIndexOf.get(question.show_when.question);
    if (target === undefined || target >= newIndex) {
      return { ...question, show_when: null };
    }
    if (target === question.show_when.question) return question;
    return { ...question, show_when: { ...question.show_when, question: target } };
  });
}

/**
 * Follow an option rename: conditions naming the old text move to the new text.
 *
 * This runs BEFORE `repairConditionsFor` on an options edit, and it is what makes
 * per-keystroke repair safe. Repair alone cleared the condition on the first keystroke
 * of a rename ("Days" -> "Day" no longer matches, condition gone) and finishing the
 * rename could not bring it back: the author lost a working rule to a typo fix, with a
 * dismissible notice as the only witness. Matching by position rather than text,
 * because the position is the one thing a keystroke does not change.
 *
 * Only exact single-option edits follow; anything else (reorder, delete, paste-over)
 * falls through to repair, which keeps what still matches and clears what cannot.
 */
export function followOptionRename(
  questions: QuestionInput[],
  changedIndex: number,
  before: string[],
  after: string[],
): QuestionInput[] {
  if (before.length !== after.length) return questions;
  const renamed = before
    .map((text, position) => ({ position, from: text, to: after[position] }))
    .filter((r) => r.from !== r.to);
  if (renamed.length !== 1) return questions;
  const { from, to } = renamed[0];

  return questions.map((question) => {
    const condition = question.show_when;
    if (!condition || condition.question !== changedIndex) return question;
    if (condition.value.toLowerCase() !== from.toLowerCase()) return question;
    return { ...question, show_when: { ...condition, value: to } };
  });
}

/**
 * Repair conditions pointing at a question whose answers have changed shape.
 *
 * A condition's value names an answer the target can actually give. Change the target's
 * type, or delete the option a condition names, and the value is left describing an
 * answer nobody can now produce. Reordering is not the only edit that orphans a
 * condition, and until this existed it was the only one handled.
 *
 * The value is kept when the target can still produce it, and the condition is cleared
 * when it cannot. Cleared rather than guessed at, for the same reason `remapConditions`
 * clears: there is no honest way to infer which of the remaining answers the author
 * meant, and a wrong guess hides a question from real respondents. Renames never reach
 * this fate, because `followOptionRename` has already moved their conditions.
 */
export function repairConditionsFor(
  questions: QuestionInput[],
  changedIndex: number,
): QuestionInput[] {
  const target = questions[changedIndex];
  if (!target) return questions;

  const stillAnswerable = (value: string): boolean => {
    if (target.options.length > 0) {
      // A write-in means the target can record something outside its own list.
      if (target.allow_other) return true;
      return target.options.some((o) => o.toLowerCase() === value.toLowerCase());
    }
    if (target.answer_type === "yes_no") {
      return ["yes", "no", "true", "false"].includes(value.toLowerCase());
    }
    // Free text, rating, number and date accept anything the author typed; the server
    // has no list to check it against either.
    return value.trim().length > 0;
  };

  return questions.map((question) => {
    const condition = question.show_when;
    if (!condition || condition.question !== changedIndex) return question;
    return stillAnswerable(condition.value) ? question : { ...question, show_when: null };
  });
}

/** How many conditions `remapConditions` had to clear — so the author can be told
 *  rather than discovering it when the survey behaves differently. */
export function clearedBy(before: QuestionInput[], after: QuestionInput[]): number {
  const had = before.filter((q) => q.show_when).length;
  const has = after.filter((q) => q.show_when).length;
  return Math.max(0, had - has);
}
