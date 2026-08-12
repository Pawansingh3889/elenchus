/**
 * Reading a stored answer into something printable.
 *
 * Answers are stored shaped per answer type, so this reads whichever key is present.
 * It replaces a copy that lived inside the results page and wrote its own English:
 * "Yes", "out of 5" and "Declined — " were hardcoded in an app that is otherwise
 * translated into eight languages, so a Polish author reading Polish answers got
 * English scaffolding around them.
 *
 * The old copy also ended in `JSON.stringify(value)`, which put a raw object in front
 * of an author whenever a shape was not recognised. An unreadable answer is a fault to
 * see, not a blob to print, so the final case says so in words instead.
 */
import type { Messages } from "@/lib/i18n";

export function readAnswer(value: Record<string, unknown>, msg: Messages): string {
  const { answers } = msg;
  if ("text" in value) return String(value.text);
  if ("rating" in value) return answers.ratingOf(Number(value.rating));
  if ("number" in value) return String(value.number);
  if ("date" in value) return String(value.date);
  if ("yes_no" in value) return value.yes_no ? answers.yes : answers.no;
  if ("option" in value) return String(value.option);
  if ("options" in value) {
    const chosen = (value.options as string[]).join(", ");
    const other = value.other ? answers.plusWriteIns((value.other as string[]).join(", ")) : "";
    return chosen + other;
  }
  if ("other" in value) return String(value.other);
  if ("unanswerable" in value) return answers.declinedBecause(String(value.unanswerable));
  return answers.unreadable;
}

/** Whether this answer is a decline rather than a value. Declines are stored as a
 *  reason under `unanswerable` rather than as a status, so every count that means
 *  "answered" has to ask this rather than checking for absence. */
export function isDecline(value: Record<string, unknown>): boolean {
  return "unanswerable" in value;
}
