import { isAllowedAnswerType, labelForAnswerType } from "@/lib/answerTypes";
import type { AnswerType, QuestionInput } from "@/lib/types";

/** The builder strings this needs, passed in rather than imported, so the rule stays a
 *  pure function of the draft and can be read without a React tree around it. */
interface Labels {
  conditionHasNoAnswer: string;
  selectHasNoOptions: string;
  typeNotAllowed: (typeLabel: string) => string;
  publishBlocker: (question: number, problem: string) => string;
}

/**
 * Why this draft cannot be published, one sentence per problem, naming the question.
 *
 * Known-bad before the server is asked. Each of these is a state the builder can reach,
 * so Publish should say why it is unavailable rather than failing after a round trip and
 * leaving the author to match "question 4" to a card by counting.
 */
export function publishBlockers(
  questions: QuestionInput[],
  allowedTypes: AnswerType[],
  labels: Labels,
): string[] {
  return questions.flatMap((q, i) => {
    const problems: string[] = [];
    // A condition with nothing to match can never be true, so the question it guards
    // would simply never appear.
    if (q.show_when && !q.show_when.value.trim()) problems.push(labels.conditionHasNoAnswer);
    // A select with nothing to choose is free text wearing a select's clothes.
    if ((q.answer_type === "single_select" || q.answer_type === "multi_select") && !q.options.length)
      problems.push(labels.selectHasNoOptions);
    // Narrowing the answer-type policy can strand a question that was legal when it was
    // written. Said here so the author sees which card to fix, not on a rejected save.
    if (!isAllowedAnswerType(q.answer_type, allowedTypes))
      problems.push(labels.typeNotAllowed(labelForAnswerType(q.answer_type)));
    return problems.map((p) => labels.publishBlocker(i + 1, p));
  });
}
