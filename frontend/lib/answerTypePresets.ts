import { ANSWER_TYPES } from "@/lib/answerTypes";
import type { AnswerType } from "@/lib/types";

/**
 * The answer-type policy as authors actually state it.
 *
 * The stored form is a whitelist of eight types, empty meaning all of them. That is the
 * right thing to store, and the wrong thing to ask for: nobody thinks "I permit
 * single_select, multi_select, yes_no, rating, number and date". They think "no text
 * questions", which is one decision, and having to express it as eight is why the
 * checkbox grid read as work rather than as an answer.
 *
 * A preset is therefore a name for a set, not a stored value. `presetFor` recognises a
 * stored set as a preset when it matches one exactly, so a policy set here and then
 * hand-edited still describes itself honestly rather than silently claiming a preset it
 * no longer matches.
 */
export type PresetKey = "any" | "no_free_text" | "closed_only" | "custom";

const FREE_TEXT: AnswerType[] = ["short_text", "long_text"];
const CLOSED: AnswerType[] = ["single_select", "multi_select", "yes_no", "rating"];

/** Empty is every type, so "any" is the empty set rather than all eight listed out.
 *  Storing all eight would mean a type added later was silently excluded from every
 *  survey that had chosen "any" before it existed. */
export const PRESET_TYPES: Record<Exclude<PresetKey, "custom">, AnswerType[]> = {
  any: [],
  no_free_text: ANSWER_TYPES.map((t) => t.value).filter((t) => !FREE_TEXT.includes(t)),
  closed_only: CLOSED,
};

const sameSet = (a: AnswerType[], b: AnswerType[]) =>
  a.length === b.length && a.every((v) => b.includes(v));

/** Which preset a stored policy is, or "custom" when it is a set of its own. */
export function presetFor(allowed: AnswerType[]): PresetKey {
  if (!allowed.length) return "any";
  if (sameSet(allowed, PRESET_TYPES.no_free_text)) return "no_free_text";
  if (sameSet(allowed, PRESET_TYPES.closed_only)) return "closed_only";
  return "custom";
}
