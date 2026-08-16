"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";
import { QuestionCard } from "@/components/results/QuestionCard";
import { RecapPanel } from "@/components/results/RecapPanel";
import { RespondentTable } from "@/components/results/RespondentTable";
import { RunPanel } from "@/components/results/RunPanel";
import { SliceControl } from "@/components/results/SliceControl";
import { Stat } from "@/components/Stat";
import { SurveyNav } from "@/components/SurveyNav";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useT } from "@/lib/i18n/useT";
import { useAnswersMatrix, useCurrentUser, useReport } from "@/lib/queries";
import { formatSlice, parseSlice, sliceRuns } from "@/lib/slicing";
import { useUserStore } from "@/lib/store";
import { tallyInputs, tallyQuestion } from "@/lib/tally";

/**
 * One page for what the survey found and who said it.
 *
 * These were two pages. Report showed per-question tallies and Responses showed one
 * respondent at a time, and nothing linked a number to a person: a verbatim on Report
 * was an anonymous string, and Responses could not say how one answer sat against the
 * rest. An author asking "did the people who said X also say Y", which is the question
 * a survey is run to answer, had no page to ask it on.
 *
 * `docs/ACCESS_AND_RESULTS.md` had already specified this shape: headline and flags
 * first, question detail below, sliceable by any closed answer.
 *
 * View state lives in the URL. `?run=` opens one response, so an author can send a
 * colleague a link to it and a refresh keeps it; it was component state before, which
 * made both impossible.
 */
function ResultsContent() {
  const msg = useT();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const search = useSearchParams();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: report, isLoading, error } = useReport(id);
  const { data: matrix } = useAnswersMatrix(id);
  const openRun = search.get("run");
  const slice = parseSlice(search.get("slice"), matrix);

  const isRespondent = currentUser ? !currentUser.may_author : false;
  useEffect(() => {
    if (isRespondent) router.replace("/respond");
  }, [isRespondent, router]);

  // replace, not push: opening responses one after another should not build a back
  // stack the author has to unwind to leave the page.
  function setParam(key: string, value: string | null) {
    const next = new URLSearchParams(search.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    router.replace(next.toString() ? `?${next}` : "?", { scroll: false });
  }

  const shown = matrix ? sliceRuns(matrix.runs, slice) : [];
  // Sliced and unsliced tallies come from the same code either way, so the page never
  // shows a server number beside a client number and invites a comparison between two
  // provenances. `lib/tally.ts` is checked against the server's own cases in vitest.
  const inputs = matrix ? tallyInputs(matrix.questions, shown) : null;
  const questions =
    inputs && matrix
      ? [...matrix.questions]
          .sort((a, b) => a.position - b.position)
          .map((q) => ({ report: tallyQuestion(inputs.get(q.id)!), runIds: inputs.get(q.id)!.runIds }))
      : [];

  if (!currentUserId) return <p className="p-6 text-muted">{msg.results.pickAuthor}</p>;
  if (isRespondent) return <p className="p-6 text-muted">{msg.home.goingToRespond}</p>;

  return (
    // The stable hook e2e/shot.mjs waits on for this page.
    <div className="results-page mx-auto flex max-w-5xl flex-col gap-4 p-4">
      <SurveyNav templateId={id} current="results" />

      {isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : null}
      {error ? <ErrorBanner error={error} /> : null}

      {report ? (
        <>
          <header className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="text-xl font-semibold">{report.title}</h1>
          </header>

          {/* Two rates, each labelled with what it is over. They were one tile reading
              "8/8 responded" beside another reading "8 responses", which is the same
              number twice, and the completion rate lived on the dashboard where there
              was no room to say what it was a share of. Here there is room. */}
          <Card className="flex flex-wrap gap-8 p-4">
            <Stat
              value={
                report.reach > 0
                  ? `${Math.round((report.people_completed / report.reach) * 100)}%`
                  : "-"
              }
              label={msg.report.rateAnswered}
              of={msg.report.ofPeopleAsked(report.people_completed, report.reach)}
            />
            <Stat
              value={
                report.runs_total > 0
                  ? `${Math.round((report.runs_completed / report.runs_total) * 100)}%`
                  : "-"
              }
              label={msg.report.rateFinished}
              of={msg.report.ofThoseWhoStarted(report.runs_completed, report.runs_total)}
            />
          </Card>

          {/* Said on the page rather than left in the code: those runs answered
              different questions under different ids, so counting them here would
              change what every number means. */}

          {/* Only when the two disagree, which is only on answers given before one
              answer per person was enforced. */}
          {report.runs_total > report.people_started ? (
            <p className="rounded-lg border border-warn-border bg-warn-fill p-3 text-sm text-warn-text">
              {msg.report.moreRunsThanPeople(report.runs_total, report.people_started)}
            </p>
          ) : null}

          {report.runs_total === 0 ? <EmptyState title={msg.report.nobodyYet} /> : null}

          {/* Headline first, per the shape the docs specified: what the survey found,
              before the question detail it was found in. Hidden under a slice, because
              the recap describes every response and would be prose about one group of
              people sitting above numbers about another. */}
          <RecapPanel
            templateId={id}
            runsCompleted={report.runs_completed}
            hidden={Boolean(slice)}
          />

          {matrix && matrix.runs.length > 0 ? (
            <SliceControl
              questions={matrix.questions}
              slice={slice}
              onChange={(next) => setParam("slice", next ? formatSlice(next) : null)}
              showing={shown.length}
              total={matrix.runs.length}
            />
          ) : null}

          {openRun ? (
            <RunPanel templateId={id} runId={openRun} onClose={() => setParam("run", null)} />
          ) : null}

          {slice && shown.length === 0 ? <EmptyState title={msg.results.sliceEmpty} /> : null}

          {matrix && shown.length > 0 ? (
            <RespondentTable
              matrix={matrix}
              runs={shown}
              openRun={openRun}
              onOpen={(runId) => setParam("run", runId)}
            />
          ) : null}

          {questions.length > 0 && shown.length > 0 ? (
            <section className="flex flex-col gap-3">
              <h2 className="text-md font-semibold">{msg.results.questionsHeading}</h2>
              {questions.map(({ report: question, runIds }, i) => (
                <QuestionCard key={question.id} question={question} position={i}>
                  {/* Counted on the page, read on click: forty open answers is a long
                      list to scroll past on the way to the next question, and grouping
                      them would mean deciding what people meant, which this is not.
                      Each one links to the response it came from, which the report
                      endpoint could not do because it drops the attribution. */}
                  {question.verbatim.length > 0 ? (
                    <details className="mt-3">
                      <summary className="cursor-pointer text-sm text-muted">
                        {msg.report.inTheirWords(question.verbatim.length)}
                      </summary>
                      <ul className="mt-2 flex flex-col gap-1 ps-4">
                        {question.verbatim.map((v, j) => (
                          <li key={j} className="list-disc text-sm">
                            {runIds[j] ? (
                              <button
                                type="button"
                                className="cursor-pointer text-start underline-offset-4 hover:underline"
                                onClick={() => setParam("run", runIds[j])}
                              >
                                {v}
                              </button>
                            ) : (
                              v
                            )}
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : null}

                  {/* Its own list, below the answers rather than mixed into them: a
                      follow-up answers a question the model wrote. */}
                  {question.follow_ups.length > 0 ? (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-sm text-muted">
                        {msg.report.whatProbesFound(question.follow_ups.length)}
                      </summary>
                      <ul className="mt-2 flex flex-col gap-1 ps-4">
                        {question.follow_ups.map((v, j) => (
                          <li key={j} className="list-disc text-sm">
                            {v}
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                </QuestionCard>
              ))}
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

export default function ResultsPage() {
  // useSearchParams needs a Suspense boundary above it, and the fallback is what shows
  // while the page's own JS arrives.
  return (
    <Suspense fallback={<div className="p-4"><Skeleton className="h-64 w-full" /></div>}>
      <ResultsContent />
    </Suspense>
  );
}
