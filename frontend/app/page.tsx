"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AutoGrowTextarea } from "@/components/AutoGrowTextarea";
import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Stat } from "@/components/Stat";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { groupForDashboard, landingFor, type Attention } from "@/lib/dashboardAttention";
import { useT } from "@/lib/i18n/useT";
import {
  useCloseTemplate,
  useCreateTemplate,
  useCurrentUser,
  useDashboard,
  useGenerateTemplate,
} from "@/lib/queries";
import { useDraftNoteStore, useUserStore } from "@/lib/store";
import type { DashboardRow } from "@/lib/types";

export default function Home() {
  const { home } = useT();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  // One request for the whole page: each survey and how it is going. The old list
  // showed a question count, which says what the survey is, not how it is doing.
  const { data: rows, isLoading, error } = useDashboard();
  const close = useCloseTemplate();
  const create = useCreateTemplate();
  const generate = useGenerateTemplate();
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const setPendingNote = useDraftNoteStore((s) => s.setPendingNote);

  // Build is author-only on the backend; a respondent landing here (e.g. after
  // switching users in the top bar) belongs on Respond, not on a page of 403s.
  const isRespondent = currentUser?.role === "respondent";
  useEffect(() => {
    if (isRespondent) router.replace("/respond");
  }, [isRespondent, router]);

  if (!currentUserId) {
    // The exact wording is asserted by e2e/smoke.spec.ts, which has no backend and so
    // can only see the signed-out state. Changing it breaks the only end-to-end proof
    // that the app renders at all.
    return <p className="p-6 text-muted">{home.pickUser}</p>;
  }
  if (isRespondent) {
    return <p className="p-6 text-muted">{home.goingToRespond}</p>;
  }

  async function onCreate() {
    // Aimed nowhere in particular until its author says so, which is what the
    // respondent pool means.
    const t = await create.mutateAsync({
      title: "Untitled survey",
      audience: "respondents",
      questions: [],
    });
    router.push(`/templates/${t.id}`);
  }

  async function onGenerate() {
    if (!prompt.trim()) return;
    const { template, note } = await generate.mutateAsync(prompt.trim());
    // Hand the note to the builder, then drop straight into it with the questions.
    if (note) setPendingNote(template.id, note);
    router.push(`/templates/${template.id}`);
  }

  const groups = rows ? groupForDashboard(rows) : null;
  // Completed runs, not people: summing people across surveys would count someone
  // asked twice as two people, and there is no distinct count to be had from rows
  // that are already aggregated per survey.
  const responses = (rows ?? []).reduce((n, r) => n + r.completed, 0);

  // The whole audience as one bar: answered, part-way, not yet. One shape instead of two
  // percentages, which is what made the old pair unreadable: the reader had to work out
  // what each was over, and the two denominators were different. Here there is one
  // denominator and the segments are three stages of the same journey through it.
  //
  // Running surveys only. A closed survey's audience cannot answer any more, so folding
  // it in would permanently drag the bar down with people nobody is waiting on.
  const audience = groups
    ? groups.running.concat(groups.needsYou.map((n) => n.row)).reduce(
        (acc, r) => ({
          surveys: acc.surveys + (r.status === "published" ? 1 : 0),
          reach: acc.reach + (r.status === "published" ? r.reach : 0),
          started: acc.started + (r.status === "published" ? r.people_started : 0),
          answered: acc.answered + (r.status === "published" ? r.people_completed : 0),
        }),
        { surveys: 0, reach: 0, started: 0, answered: 0 },
      )
    : null;
  // max() rather than reach alone: an author testing their own respondent-aimed survey
  // answers it without being in its audience, so answered can exceed reach and a bar
  // divided by reach would overflow its own track. Widening the denominator to fit keeps
  // the segments summing to the whole, which is the one property a part-to-whole bar has.
  const asked = audience ? Math.max(audience.reach, audience.started, 1) : 1;
  const partWay = audience ? Math.max(0, audience.started - audience.answered) : 0;
  const notYet = audience ? Math.max(0, asked - audience.started) : 0;
  const share = (n: number) => Math.round((n / asked) * 100);

  // The line under each row. Reach is the denominator throughout, so there is one
  // percentage on this page and it is always "of the people it was for". Completion,
  // which is a share of whoever turned up, lives on the results page where there is
  // room to say so.
  const reachLine = (r: DashboardRow) =>
    r.reach > 0 ? home.ofPeople(r.people_completed, r.reach) : home.noResponses;

  const why = (row: DashboardRow, attention: Attention) => {
    if (attention === "resultsReady") return home.whyResultsReady;
    if (attention === "nobodyYet") return home.whyNobodyYet;
    if (attention === "stalled") return home.whyStalled(row.in_progress);
    return home.whyNotPublished;
  };

  const closeButton = (r: DashboardRow) => (
    // Closing is the only way to retire a published survey: it cannot be deleted,
    // because its frozen versions are what real answers point at.
    <Button
      variant="quiet"
      size="sm"
      onClick={() => close.mutate(r.id)}
      disabled={close.isPending}
    >
      {close.isPending && close.variables === r.id ? home.closing : home.closeSurvey}
    </Button>
  );

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 p-4">
      {/* No page heading: the top bar already says Dashboard, and repeating it spent a
          row of vertical space saying where you are to someone who just clicked to get
          here. The compose bar is the first thing instead, which is the first thing an
          author does.

          Describing a survey and having it drafted is the most distinctive thing this
          product does, and putting it under the work made it the least visible. A bar
          rather than a card: one line that grows as you type, so the summary below it
          stays above the fold. */}
      <div className="flex flex-col gap-2 rounded-lg border border-ai-border bg-ai-fill p-2">
        {/* Three lines at rest: a one-line box invites a phrase, and the model drafts a
            better survey from a description. The button sits under the box rather than
            beside it, because beside a three-line input it takes width the description
            wants and leaves a column of empty space under itself. */}
        <AutoGrowTextarea
          className="autogrow min-h-[4.6rem] w-full rounded-md border border-line bg-raised px-2.5 py-2"
          placeholder={home.describePlaceholder}
          value={prompt}
          onChange={setPrompt}
        />
        {/* Both ways of starting a survey sit together: describe it and have it drafted,
            or open an empty builder. The blank one is the quieter of the two because it
            is the longer road, but it stays reachable rather than being removed with the
            page heading it happened to share a row with. */}
        <div className="flex flex-wrap items-center justify-end gap-2">
          <Button variant="quiet" size="sm" onClick={onCreate} disabled={create.isPending}>
            {create.isPending ? home.creating : home.newSurvey}
          </Button>
          <Button
            variant="ai"
            onClick={onGenerate}
            disabled={generate.isPending || !prompt.trim()}
          >
            {generate.isPending ? home.drafting : home.generateDraft}
          </Button>
        </div>
      </div>

      {generate.error ? <ErrorBanner error={generate.error} /> : null}
      {create.error ? <ErrorBanner error={create.error} /> : null}
      {error ? <ErrorBanner error={error} /> : null}

      {isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : null}

      {groups && audience && audience.surveys > 0 ? (
        <Card className="flex flex-col gap-3 p-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="text-xs uppercase tracking-wide text-muted">
              {home.bandTitle(audience.surveys)}
            </p>
          </div>

          <div className="flex flex-wrap gap-6">
            <Stat value={groups.needsYou.length} label={home.surveysNeedingYou} />
            <Stat value={groups.running.length} label={home.surveysRunning} />
            <Stat value={responses} label={home.responsesIn} />
          </div>

          {/* Three stages of one journey through one audience, so a single hue getting
              darker as it gets further along rather than three unrelated colours. The
              2px gaps are the surface showing through, which keeps two adjacent shades
              from reading as one block. A div bar rather than a charting component: one
              stacked bar has no axis to draw and would not earn the mount. */}
          <div
            className="flex h-3.5 gap-0.5 overflow-hidden rounded-full bg-canvas"
            role="img"
            aria-label={home.bandAria(share(audience.answered), share(partWay), share(notYet))}
          >
            <span
              className="bg-accent-strong"
              style={{ inlineSize: `${share(audience.answered)}%` }}
            />
            <span className="bg-accent" style={{ inlineSize: `${share(partWay)}%` }} />
            <span className="bg-muted-light" style={{ inlineSize: `${share(notYet)}%` }} />
          </div>

          {/* Every segment is named and counted here, so the bar is never the only thing
              carrying the meaning: the same reason each bar elsewhere is direct-labelled. */}
          <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
            {[
              { swatch: "bg-accent-strong", pct: share(audience.answered), label: home.segAnswered, n: audience.answered },
              { swatch: "bg-accent", pct: share(partWay), label: home.segPartWay, n: partWay },
              { swatch: "bg-muted-light", pct: share(notYet), label: home.segNotYet, n: notYet },
            ].map((seg) => (
              <span key={seg.label} className="flex items-center gap-1.5">
                <span className={`size-2.5 shrink-0 rounded-sm ${seg.swatch}`} aria-hidden />
                <b className="tabular-nums">{seg.pct}%</b>
                <span className="text-muted">{seg.label}</span>
                <span className="text-muted tabular-nums">{seg.n}</span>
              </span>
            ))}
          </div>

          {/* Said on the page rather than left as a puzzle: reach is summed per survey,
              so a person in two audiences is two of this number. Only shown when it can
              actually be happening. */}
          {audience.surveys > 1 ? (
            <p className="text-xs text-muted">{home.countedPerSurvey}</p>
          ) : null}
        </Card>
      ) : null}

      {groups && groups.needsYou.length > 0 ? (
        <section className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-md font-semibold">
            {home.groupNeedsYou}
            <Badge variant="warn">{groups.needsYou.length}</Badge>
          </h2>
          {groups.needsYou.map(({ row: r, why: attention }) => (
            // `template-row` is the selector e2e/shot.mjs waits for before taking a
            // screenshot. It carries no styling now and is kept as that hook.
            <Card
              key={r.id}
              className="template-row flex flex-wrap items-center gap-3 border-s-2 border-s-highlight p-3"
            >
              <Link href={landingFor(r)} className="min-w-0 flex-1 no-underline">
                <span className="block truncate font-medium text-ink">{r.title}</span>
                <span className="block text-sm text-warn-text">{why(r, attention)}</span>
              </Link>
              <div className="flex items-center gap-2">
                {attention === "resultsReady" ? (
                  <Button variant="primary" size="sm" asChild>
                    <Link href={`/templates/${r.id}/results`}>{home.readResults}</Link>
                  </Button>
                ) : (
                  <Button variant="secondary" size="sm" asChild>
                    <Link href={`/templates/${r.id}`}>{home.openBuilder}</Link>
                  </Button>
                )}
                {r.status === "published" ? closeButton(r) : null}
              </div>
            </Card>
          ))}
        </section>
      ) : null}

      {groups && groups.running.length > 0 ? (
        <section className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-md font-semibold">
            {home.groupRunning}
            <Badge>{groups.running.length}</Badge>
            {groups.needsYou.length === 0 ? (
              <span className="text-sm font-normal text-muted">{home.allRunning}</span>
            ) : null}
          </h2>
          {groups.running.map((r) => (
            <Card key={r.id} className="template-row flex flex-wrap items-center gap-3 p-3">
              <Link href={landingFor(r)} className="min-w-0 flex-1 no-underline">
                <span className="block truncate font-medium text-ink">{r.title}</span>
                <span className="block text-sm text-muted">
                  {reachLine(r)}
                  {r.in_progress > 0 ? ` · ${r.in_progress} ${home.inProgress}` : ""}
                  {/* Only when the two disagree, which is only on rows written before
                      one answer per person was enforced. It shrinks to nothing on its
                      own rather than being a permanent feature of the page. */}
                  {r.started > r.people_started
                    ? ` · ${home.runsFromPeople(r.started, r.people_started)}`
                    : ""}
                </span>
              </Link>
              {/* One ratio against a limit, so a meter rather than a number: the bar is
                  comparable down the column at a glance and the figure beside it is the
                  finding. A dash, not 0%, when nobody has started: the rate is null
                  there, and 0% would read as everyone refusing. */}
              <div className="flex w-32 items-center gap-2" title={reachLine(r)}>
                <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted-light">
                  <span
                    className="block h-full rounded-full bg-accent-strong"
                    style={{
                      inlineSize: `${Math.min(100, Math.round((r.response_rate ?? 0) * 100))}%`,
                    }}
                  />
                </span>
                <span className="w-9 text-end text-sm tabular-nums text-muted">
                  {r.response_rate === null ? "-" : `${Math.round(r.response_rate * 100)}%`}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {r.completed > 0 ? (
                  <Button variant="secondary" size="sm" asChild>
                    <Link href={`/templates/${r.id}/results`}>{home.report}</Link>
                  </Button>
                ) : null}
                {closeButton(r)}
              </div>
            </Card>
          ))}
        </section>
      ) : null}

      {groups && groups.closed.length > 0 ? (
        <section className="flex flex-col gap-2">
          <h2 className="flex items-center gap-2 text-md font-semibold">
            {home.groupClosed}
            <Badge>{groups.closed.length}</Badge>
          </h2>
          {groups.closed.map((r) => (
            <Card key={r.id} className="template-row flex flex-wrap items-center gap-3 p-3 opacity-75">
              <Link href={landingFor(r)} className="min-w-0 flex-1 no-underline">
                <span className="block truncate font-medium text-ink">{r.title}</span>
                <span className="block text-sm text-muted">{reachLine(r)}</span>
              </Link>
              {r.completed > 0 ? (
                <Button variant="secondary" size="sm" asChild>
                  <Link href={`/templates/${r.id}/results`}>{home.report}</Link>
                </Button>
              ) : null}
            </Card>
          ))}
        </section>
      ) : null}

      {rows && rows.length === 0 ? <EmptyState title={home.empty} /> : null}
    </div>
  );
}
