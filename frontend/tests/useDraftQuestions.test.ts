import { act, renderHook } from "@testing-library/react";
import { expect, test } from "vitest";

import { useDraftQuestions } from "@/lib/useDraftQuestions";
import type { QuestionInput } from "@/lib/types";

const question = (text: string, over: Partial<QuestionInput> = {}): QuestionInput => ({
  text,
  answer_type: "single_select",
  options: ["Line lead", "Quality manager"],
  allow_other: false,
  required: true,
  allow_follow_ups: false,
  show_when: null,
  ...over,
});

/**
 * Deleting a conditional question told the author a condition had been cleared.
 *
 * `dropped` drives a notice reading "1 visibility condition removed: the question it
 * referred to was deleted or no longer comes before it." That is a report of collateral
 * damage, and it was firing on the author's own deliberate delete: `clearedBy` compares
 * how many conditions the list had before and after, and the deleted question took its
 * own condition out of the count. Nothing was repaired; a row went away.
 *
 * The distinction matters because the notice is the only witness to a real repair. One
 * that cries wolf on every delete is one an author learns to dismiss without reading.
 */
test("deleting a question that has a condition is not a cleared condition", () => {
  const { result } = renderHook(() => useDraftQuestions());

  act(() =>
    result.current.reset([
      question("What is your role?"),
      question("Which shift?", { show_when: { question: 0, op: "is", value: "Line lead" } }),
    ]),
  );

  // Delete the conditional question itself. Nothing else points anywhere.
  act(() => result.current.remove(1));

  expect(result.current.questions).toHaveLength(1);
  expect(result.current.dropped).toBe(0);
});

/**
 * The counterpart, so the fix cannot be "always report zero on delete". Deleting the
 * TARGET of a condition really does orphan the question that pointed at it, and the
 * author needs telling: their rule is gone and the question now shows to everyone.
 */
test("deleting the question a condition points at is reported", () => {
  const { result } = renderHook(() => useDraftQuestions());

  act(() =>
    result.current.reset([
      question("What is your role?"),
      question("Which shift?", { show_when: { question: 0, op: "is", value: "Line lead" } }),
    ]),
  );

  act(() => result.current.remove(0));

  expect(result.current.questions).toHaveLength(1);
  expect(result.current.questions[0].show_when).toBeNull();
  expect(result.current.dropped).toBe(1);
});

/**
 * And the mixed case, which is where the old count went furthest wrong: deleting a
 * question that both carries a condition and is the target of another reported 2, when
 * exactly one condition was actually lost.
 */
test("a delete that is both conditional and a target reports only what was orphaned", () => {
  const { result } = renderHook(() => useDraftQuestions());

  act(() =>
    result.current.reset([
      question("What is your role?"),
      question("Which shift?", { show_when: { question: 0, op: "is", value: "Line lead" } }),
      question("How cold was the store?", { show_when: { question: 1, op: "is", value: "Nights" } }),
    ]),
  );

  act(() => result.current.remove(1));

  expect(result.current.questions).toHaveLength(2);
  expect(result.current.questions[1].show_when).toBeNull();
  expect(result.current.dropped).toBe(1);
});
