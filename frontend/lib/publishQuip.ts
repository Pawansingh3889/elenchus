import type { QuestionInput } from "./types";

/**
 * A dry aside for the publish dialog, chosen from what the author has actually built.
 *
 * English only, and deliberately outside the i18n messages. Every other string in the
 * app is a key that all eight locales must carry, which is the right rule for anything
 * load-bearing and the wrong one for a joke: a line translated by someone who cannot
 * hear it lands somewhere between flat and odd, and there is no way to check it. The
 * dialog says everything that matters through the normal message keys, in every locale.
 * This is the one line that is decoration, so it is allowed to be absent.
 *
 * Returns null when there is nothing worth saying, which is also what every non-English
 * locale gets.
 */
export function publishQuip(
  questions: QuestionInput[],
  republishing: boolean,
  locale: string,
): string | null {
  if (locale !== "en") return null;

  const count = questions.length;
  const probing = questions.filter((q) => q.follow_up_policy === "always_once").length;

  // Ordered by how much the author would want to hear it, not by how funny it is. A
  // survey that probes on every question is the one most likely to be abandoned
  // half-answered, so it gets the line even when it is also long or also a republish.
  if (probing > 0 && probing === count && count > 1) {
    return "Every single question asks a follow-up. Your respondents will feel very heard, and very tired.";
  }
  if (count >= 10) {
    return `${count} questions. Be honest: would you finish this on your phone, on a break?`;
  }
  if (count === 1) {
    return "One question. Admirably restrained.";
  }
  if (republishing) {
    return "Round two. The last version also seemed like a good idea at the time.";
  }
  return null;
}
