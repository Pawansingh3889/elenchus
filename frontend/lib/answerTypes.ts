/**
 * The answer types a question can be, in the order the builder offers them.
 *
 * Shared rather than inlined in the question editor, because the live preview labels a
 * question by the same names and the two must not drift.
 */
import type { AnswerType } from "@/lib/types";

export const ANSWER_TYPES: { value: AnswerType; label: string }[] = [
  { value: "single_select", label: "Single select" },
  { value: "multi_select", label: "Multi select" },
  { value: "yes_no", label: "Yes / No" },
  { value: "short_text", label: "Short text" },
  { value: "long_text", label: "Long text" },
  { value: "rating", label: "Rating (1–5)" },
  { value: "number", label: "Number" },
  { value: "date", label: "Date" },
];

export const labelForAnswerType = (t: AnswerType) =>
  ANSWER_TYPES.find((x) => x.value === t)?.label ?? t;
