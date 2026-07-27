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

/** How many conditions `remapConditions` had to clear — so the author can be told
 *  rather than discovering it when the survey behaves differently. */
export function clearedBy(before: QuestionInput[], after: QuestionInput[]): number {
  const had = before.filter((q) => q.show_when).length;
  const has = after.filter((q) => q.show_when).length;
  return Math.max(0, had - has);
}
