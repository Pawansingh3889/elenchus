"use client";

import { X } from "lucide-react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Transcript } from "@/components/Transcript";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardLabel } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { readAnswer } from "@/lib/answers";
import { useT } from "@/lib/i18n/useT";
import { useTemplateRun } from "@/lib/queries";
import type { RunAnswer, RunDetail } from "@/lib/types";

/** One question's answer and whatever the follow-ups drew out of it.
 *
 *  Grouped rather than listed flat, because a follow-up answers a question the model
 *  wrote and showing it at the same level would credit the author's question with words
 *  it never asked for. */
function groupByQuestion(answers: RunAnswer[]) {
  const order: string[] = [];
  const groups = new Map<string, { scripted?: RunAnswer; followUps: RunAnswer[] }>();
  for (const answer of answers) {
    if (!groups.has(answer.question_id)) {
      groups.set(answer.question_id, { followUps: [] });
      order.push(answer.question_id);
    }
    const group = groups.get(answer.question_id)!;
    if (answer.kind === "scripted") group.scripted = answer;
    else group.followUps.push(answer);
  }
  return order.map((questionId) => ({ questionId, ...groups.get(questionId)! }));
}

function totalProbes(run: RunDetail): number {
  return Object.values(run.follow_ups_asked ?? {}).reduce((n, count) => n + count, 0);
}

/**
 * One respondent's whole response, opened beside the numbers.
 *
 * Reached through `?run=` rather than component state, so the view is a URL: an author
 * can link a colleague to one person's answers, and a refresh does not lose the
 * selection. It was `useState` before, which made both impossible.
 */
export function RunPanel({
  templateId,
  runId,
  onClose,
}: {
  templateId: string;
  runId: string;
  onClose: () => void;
}) {
  const msg = useT();
  const { data: run, isLoading, error } = useTemplateRun(templateId, runId);

  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <CardLabel>{msg.results.answers}</CardLabel>
          <p className="text-md font-semibold">{run?.respondent_label ?? "…"}</p>
        </div>
        <Button variant="quiet" size="sm" onClick={onClose} aria-label={msg.results.closePanel}>
          <X aria-hidden />
        </Button>
      </div>

      {isLoading ? <Skeleton className="h-40 w-full" /> : null}
      {error ? <ErrorBanner error={error} /> : null}

      {run ? (
        <>
          <p className="text-sm text-muted">
            {msg.results.startedOn(new Date(run.started_at).toLocaleString())} ·{" "}
            {run.completed_at
              ? msg.results.completedOn(new Date(run.completed_at).toLocaleString())
              : msg.results.stillGoing}
            {/* Run-level, as well as the per-question chips: a question that was probed
                but never answered has no row to hang a chip on. */}
            {totalProbes(run) > 0 ? ` · ${msg.results.probesAsked(totalProbes(run))}` : ""}
          </p>

          <div className="flex flex-col gap-3">
            {groupByQuestion(run.answers).map((group) => (
              <div key={group.questionId} className="border-s-2 border-line ps-3">
                <p className="flex flex-wrap items-center gap-2 text-sm text-muted">
                  {group.scripted?.question_text ?? msg.results.unansweredQuestion}
                  {run.follow_ups_asked?.[group.questionId] ? (
                    <Badge variant="accent" title={msg.results.probeHint}>
                      {msg.results.probedChip(run.follow_ups_asked[group.questionId])}
                    </Badge>
                  ) : null}
                </p>
                {group.scripted ? (
                  <p className="text-ink">{readAnswer(group.scripted.value, msg)}</p>
                ) : (
                  <p className="text-sm text-muted">{msg.results.notAnswered}</p>
                )}
                {group.followUps.map((followUp, i) => (
                  <div key={`${group.questionId}-${i}`} className="mt-2 ps-3">
                    <p className="flex flex-wrap items-center gap-2 text-sm text-muted">
                      {followUp.question_text}
                      <Badge variant="accent">{msg.results.followUp}</Badge>
                    </p>
                    <p className="text-ink">{readAnswer(followUp.value, msg)}</p>
                  </div>
                ))}
              </div>
            ))}
            {run.answers.length === 0 ? (
              <p className="text-sm text-muted">{msg.results.nothingAnswered}</p>
            ) : null}
          </div>

          <div>
            <CardLabel>{msg.results.transcript}</CardLabel>
            <Transcript messages={run.messages} flat />
          </div>
        </>
      ) : null}
    </Card>
  );
}
