"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";
import { FlagStrip } from "@/components/results/FlagStrip";
import { QuestionCard } from "@/components/results/QuestionCard";
import { QuestionRail } from "@/components/results/QuestionRail";
import { RecapPanel } from "@/components/results/RecapPanel";
import { RespondentTable } from "@/components/results/RespondentTable";
import { RespondentTracker } from "@/components/results/RespondentTracker";
import { RunPanel } from "@/components/results/RunPanel";
import { ControlBar } from "@/components/results/ControlBar";
import { Stat } from "@/components/Stat";
import { SurveyNav } from "@/components/SurveyNav";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useT } from "@/lib/i18n/useT";
import { useAnswersMatrix, useCurrentUser, useReport } from "@/lib/queries";
import { formatSlice, parseSlice, sliceRuns } from "@/lib/slicing";
import { useUserStore } from "@/lib/store";
import { groupRuns } from "@/lib/comparison";
import { flagsFor } from "@/lib/flags";
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
  //
  // Several keys in one call, because two calls in one handler both start from the
  // params of the current render, and the second silently undoes the first.
  function setParams(changes: Record<string, string | null>) {
    const next = new URLSearchParams(search.toString());
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    router.replace(next.toString() ? `?${next}` : "?", { scroll: false });
  }
  const setParam = (key: string, value: string | null) => setParams({ [key]: value });

  const compareBy = search.get("compare");
  const shown = matrix ? sliceRuns(matrix.runs, slice) : [];
  // Sliced and unsliced tallies come from the same code either way, so the page never
  // shows a server number beside a client number and invites a comparison between two
  // provenances. `lib/tally.ts` is checked against the server's own cases in vitest.
  const inputs = matrix ? tallyInputs(matrix.questions, shown) : null;

  // Comparison. Colour on this page carries one thing: which group of people a bar
  // belongs to. Picking a question here splits the shown runs by how each person
  // answered it, and every card below then draws one bar per group.
  //
  // Four groups at most, because the series palette is four and a fifth hue would
  // either read grey or borrow the amber that status is rationed to. The rest fold into
  // one "other" bar rather than disappearing, and the control says so.
  const compareQuestion = matrix?.questions.find((q) => q.id === compareBy) ?? null;
  const groups = compareQuestion ? groupRuns(shown, compareQuestion) : [];
  const questions =
    inputs && matrix
      ? [...matrix.questions]
          .sort((a, b) => a.position - b.position)
          .map((q) => ({
            report: tallyQuestion(inputs.get(q.id)!),
            runIds: inputs.get(q.id)!.runIds,
            // One tally per group, from the same function the whole-survey tally uses,
            // so a series and the bar behind it can never come from two code paths.
            series: groups.map((g) => ({
              label: g.label,
              report: tallyQuestion(tallyInputs(matrix.questions, g.runs).get(q.id)!),
            })),
          }))
      : [];

  // From the same tallies the cards below draw, so the strip can never name a finding
  // the chart it points at does not show. Recomputed under a slice rather than kept from
  // the whole survey: while a slice is showing, every number on the page is about those
  // people, and a flag from the other group would be the one thing that is not.
  const flags = flagsFor(questions.map((q) => q.report));
  const flagged = new Set(flags.map((f) => f.questionId));

  if (!currentUserId) return <p className="p-6 text-muted">{msg.results.pickAuthor}</p>;
  if (isRespondent) return <p className="p-6 text-muted">{msg.home.goingToRespond}</p>;

  return (
    // results-page is what globals.css widens the shell for, via :has. It used to be
    // the hook a Playwright screenshot script waited on; that script went with the
    // browser suite in 2f56dfb, so the class earns its place from the stylesheet now.
    <div className="results-page mx-auto flex max-w-7xl flex-col gap-4 p-4">
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

          {/* The slicers, above everything they act on, and sticky, so the state of the
              page can be read from any scroll position. What every BI tool does with its
              filter band, and for the reason they do it: a filtered number with no
              visible filter gets quoted as the whole. */}
          {matrix && matrix.runs.length > 0 ? (
            <ControlBar
              questions={matrix.questions}
              slice={slice}
              onSlice={(next) => setParam("slice", next ? formatSlice(next) : null)}
              compareBy={compareBy}
              onCompare={(next) => setParam("compare", next)}
              onClear={() => setParams({ slice: null, compare: null })}
              groups={groups.map((g) => g.label)}
              showing={shown.length}
              total={matrix.runs.length}
            />
          ) : null}

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
            {/* A count rather than a rate, because it is not a share of anything: it is
                how many questions are worth reading first. Absent when there are none,
                so a clean survey does not carry a permanent "0 flagged" that trains the
                reader to skip the row. */}
            {flags.length > 0 ? (
              <Stat
                value={flags.length}
                label={msg.report.rateFlagged}
                of={msg.report.ofQuestions(questions.length)}
                className="text-warn-text"
              />
            ) : null}
          </Card>

          <FlagStrip flags={flags} />

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

          {openRun ? (
            <RunPanel templateId={id} runId={openRun} onClose={() => setParam("run", null)} />
          ) : null}

          {slice && shown.length === 0 ? <EmptyState title={msg.results.sliceEmpty} /> : null}

          {questions.length > 0 && shown.length > 0 ? (
            /* The rail beside what it points at, and the respondent table below the
               charts rather than above them: aggregate first, then the rows behind it,
               which is the order every results dashboard settles on and the order an
               author reads in. min-w-0 so the table inside can scroll rather than
               stretching the column to its own width. */
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:gap-6">
              <QuestionRail
                questions={questions.map(({ report: q }) => ({ id: q.id, text: q.text }))}
                flagged={flagged}
              />

              <div className="flex min-w-0 flex-1 flex-col gap-4">
                <section className="flex flex-col gap-3">
                  <h2 className="text-md font-semibold">{msg.results.questionsHeading}</h2>
                  {/* Tiles, not a column. One card per row spent 992px on a bar for a
                      count of one and made eight questions five screens tall. Two columns
                      from lg up; a card decides its own span (see QuestionCard), and the
                      grid is not dense, so Q4 never appears above Q3 to fill a gap. */}
                  <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                    {questions.map(({ report: question, runIds, series }, i) => (
                      <QuestionCard
                        key={question.id}
                        question={question}
                        position={i}
                        series={compareQuestion && compareQuestion.id !== question.id ? series : []}
                        flagged={flagged.has(question.id)}
                        slice={slice}
                        onSlice={(next) => setParam("slice", next ? formatSlice(next) : null)}
                        pageComparing={Boolean(compareQuestion)}
                      >
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
                  </div>
                </section>

                {/* Real-time respondent tracking */}
                <RespondentTracker templateId={id} />

                {matrix && shown.length > 0 ? (
                  <RespondentTable
                    matrix={matrix}
                    runs={shown}
                    openRun={openRun}
                    onOpen={(runId) => setParam("run", runId)}
                  />
                ) : null}
              </div>
            </div>
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
