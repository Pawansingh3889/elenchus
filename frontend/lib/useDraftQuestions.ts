"use client";

import { useState } from "react";

import { clearedBy, followOptionRename, remapConditions, repairConditionsFor } from "@/lib/conditions";
import type { AnswerType, QuestionInput } from "@/lib/types";

/**
 * The draft's question list, and the condition repair every edit to it has to perform.
 *
 * Extracted from the builder page because this is a small state machine rather than
 * markup: conditions are keyed by position, so adding, deleting, reordering and even
 * editing a question can orphan a *later* question's condition, and each of the four
 * mutations has to repair the rest of the list. Kept together, the rule that a condition
 * must always point at an earlier question that can still answer it is enforced in one
 * place instead of four.
 *
 * `dropped` counts what the last edit had to clear, so the page can say so rather than
 * silently dropping the author's work.
 */
export function useDraftQuestions() {
  const [questions, setQuestions] = useState<QuestionInput[]>([]);
  const [dropped, setDropped] = useState(0);

  /** Replace the whole list without counting anything as cleared: loading a template or
   *  taking the AI's revision is not an edit the author made and has no repair to report. */
  const reset = (next: QuestionInput[]) => {
    setQuestions(next);
    setDropped(0);
  };

  // Editing a question can orphan a later question's condition: change the type and the
  // options go, remove an option and a condition naming it describes an answer that can
  // no longer be given. Repositioning is not the only edit conditions depend on.
  //
  // An option RENAME is followed before repair judges anything. This runs on every
  // keystroke, so "Days" being edited to "Nights" passes through "Day", "Da"… and a
  // repair-only pass cleared the condition at the first non-matching keystroke, then had
  // no way to restore it when the author finished typing.
  const patch = (i: number, changes: Partial<QuestionInput>) =>
    setQuestions((qs) => {
      const patched = qs.map((q, j) => (j === i ? { ...q, ...changes } : q));
      const touchesAnswers =
        "answer_type" in changes || "options" in changes || "allow_other" in changes;
      if (!touchesAnswers) return patched;
      const followed =
        "options" in changes && changes.options
          ? followOptionRename(patched, i, qs[i].options, changes.options)
          : patched;
      const next = repairConditionsFor(followed, i);
      setDropped(clearedBy(followed, next));
      return next;
    });

  /** A new card, seeded with the first type the survey actually permits so adding a
   *  question to a survey that bans free text does not seed one the author cannot save. */
  const add = (allowed: AnswerType[]) =>
    setQuestions((qs) => [
      ...qs,
      {
        text: "",
        answer_type: allowed.length ? allowed[0] : "short_text",
        options: [],
        allow_other: false,
        required: true,
        allow_follow_ups: false,
        show_when: null,
      },
    ]);

  // Deleting and reordering both shift positions, and conditions are keyed by position,
  // so both have to repoint them or a condition silently starts referring to whatever
  // question moved into that slot. One helper, given the new order.
  const reorderedTo = (order: number[]) =>
    setQuestions((qs) => {
      const next = remapConditions(
        order.map((j) => qs[j]),
        order,
      );
      setDropped(clearedBy(qs, next));
      return next;
    });

  const remove = (i: number) =>
    setQuestions((qs) => {
      const order = qs.map((_, j) => j).filter((j) => j !== i);
      const next = remapConditions(
        order.map((j) => qs[j]),
        order,
      );
      setDropped(clearedBy(qs, next));
      return next;
    });

  const move = (i: number, direction: number) => {
    const j = i + direction;
    if (j < 0 || j >= questions.length) return;
    const order = questions.map((_, k) => k);
    [order[i], order[j]] = [order[j], order[i]];
    reorderedTo(order);
  };

  return {
    questions,
    dropped,
    dismissDropped: () => setDropped(0),
    reset,
    patch,
    add,
    remove,
    move,
  };
}
