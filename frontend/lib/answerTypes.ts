/**
 * The answer types an author can choose from, in the order they are offered.
 *
 * Shared rather than owned by the question editor, because the answer-type policy panel
 * offers the same list and the two must not drift: a type the policy cannot tick is a
 * type no question can ever use, and a type the policy allows but the dropdown omits is
 * a rule about nothing.
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

/** Empty is every type, not "unset", so an author who has set no policy is unrestricted. */
export const isAllowedAnswerType = (t: AnswerType, allowed: AnswerType[]) =>
  allowed.length === 0 || allowed.includes(t);
