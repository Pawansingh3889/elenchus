import type { QuestionReport } from "./types";

/**
 * The questions worth looking at first, decided from the answers alone.
 *
 * A report of twelve questions is twelve charts, and an author scrolling them has to
 * hold every shape in their head to notice the one that matters. This picks that one
 * out, and it is the only place on the report where a status colour is allowed: amber is
 * rationed so that it still means something when it appears, which is why the series
 * palette stops at four hues rather than borrowing it for a fifth group.
 *
 * **A flag is a fact about the answers, never a judgement about the plant.** That rules
 * out more than it allows, and the exclusions are the design:
 *
 * - **A number is never flagged.** A chiller at 6C is a chill-chain breach and six years
 *   of service is not, and nothing in the schema tells these apart: a question carries
 *   its text and its type, and no safe range. Flagging "above 5" would be the app
 *   inventing a limit and then attributing it to the survey. The day questions carry a
 *   range the author sets, this is where that flag goes.
 * - **A yes/no majority is never flagged.** "Was PPE available?" answered no is bad and
 *   "Did you have any problems?" answered no is good, and the question text is the only
 *   thing that separates them, which means reading it, which means guessing.
 *
 * What is left are two findings that hold whatever the question was about.
 */

export type FlagKind = "declined" | "lowRating";

export interface Flag {
  questionId: string;
  /** Position in the report as printed, so the strip and the cards below agree. */
  position: number;
  text: string;
  kind: FlagKind;
  /** How many people the flag is about, and out of how many it reached. */
  count: number;
  of: number;
  /** The rating average, on a low-rating flag only. */
  average: number | null;
}

/**
 * Two people, so a flag is about the question rather than about one person.
 *
 * One respondent declining is a fact and the card already prints it; calling it a
 * finding about the question would put "everyone refused" above a survey one person has
 * opened. A flag that fires on a sample of one gets ignored, and an ignored flag is worse
 * than no flag, because the amber is spent.
 */
const MIN_RESPONSES = 2;

/**
 * The bottom two steps of the 1-5 scale.
 *
 * A threshold over the app's own scale rather than over anything in the world: whatever
 * the question asked, an average of 2 or less means most people answered near the bottom
 * of the five steps this app defines. Deliberately below the midpoint rather than at it,
 * because a flag on every below-average rating is a flag on about half of them.
 */
const LOW_RATING = 2;

export function flagsFor(questions: QuestionReport[]): Flag[] {
  const flags: Flag[] = [];

  questions.forEach((question, position) => {
    const reached = question.answered + question.declined;
    const here = { questionId: question.id, position, text: question.text };

    // At most one line per question, and the refusal wins when both apply. Partly so the
    // strip is a list of questions and the tile above can count them without the two
    // numbers disagreeing, but mostly because the two facts are not equal when they
    // coincide: if half the room would not answer, the average is over whoever remained,
    // and "the rating was low" said of that remnant is the weaker half of the finding.
    // Both numbers are still on the card, which is where the strip sends the reader.
    if (reached >= MIN_RESPONSES && question.declined * 2 >= reached) {
      // Asked, and refused by half the room. True of any question type, including the
      // two whose answers are never flagged: what people would not say is a finding on
      // its own, and it is the one this page could not show before, because a question
      // everybody skipped drew an empty chart that read like a question nobody reached.
      flags.push({
        ...here,
        kind: "declined",
        count: question.declined,
        of: reached,
        average: null,
      });
    } else if (
      question.answer_type === "rating" &&
      question.average !== null &&
      question.average <= LOW_RATING &&
      question.answered >= MIN_RESPONSES
    ) {
      flags.push({
        ...here,
        kind: "lowRating",
        count: question.answered,
        of: question.answered,
        average: question.average,
      });
    }
  });

  // Question order, not severity order. The strip is a way into the page below, and a
  // reader following it should move down the report rather than jump about it.
  return flags;
}
