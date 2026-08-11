"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  useCloseTemplate,
  useCreateTemplate,
  useCurrentUser,
  useDashboard,
  useGenerateTemplate,
} from "@/lib/queries";
import { AutoGrowTextarea } from "@/components/AutoGrowTextarea";
import { groupForDashboard, landingFor, type Attention } from "@/lib/dashboardAttention";
import { useT } from "@/lib/i18n/useT";
import { useDraftNoteStore, useUserStore } from "@/lib/store";
import type { DashboardRow } from "@/lib/types";

export default function Home() {
  const { common, home } = useT();
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
    return <div className="empty">{home.pickUser}</div>;
  }
  if (isRespondent) {
    return <div className="empty">{home.goingToRespond}</div>;
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

  // Three numbers, and each answers a different question. The old row had six, two of
  // which ("Surveys" and "Published") were the same number on every screen anyone has
  // looked at, and two of which were percentages sitting side by side with no way to
  // tell which was over what.
  const groups = rows ? groupForDashboard(rows) : null;
  const totals = groups
    ? {
        needsYou: groups.needsYou.length,
        running: groups.running.length,
        // Completed runs, not people: summing people across surveys would count someone
        // asked twice as two people, and there is no distinct count to be had from rows
        // that are already aggregated per survey.
        responses: (rows ?? []).reduce((n, r) => n + r.completed, 0),
      }
    : null;

  // The whole audience as one bar: answered, part-way, not yet. One shape instead of two
  // percentages, which is what made the old pair unreadable — the reader had to work out
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
  // which is a share of whoever turned up, lives on the report where there is room to
  // say so.
  const reachLine = (r: DashboardRow) =>
    r.reach > 0 ? home.ofPeople(r.people_completed, r.reach) : home.noResponses;

  const why = (row: DashboardRow, attention: Attention) => {
    if (attention === "resultsReady") return home.whyResultsReady;
    if (attention === "nobodyYet") return home.whyNobodyYet;
    if (attention === "stalled") return home.whyStalled(row.in_progress);
    return home.whyNotPublished;
  };

  const draftBar = (
    <div className="draft-bar">
      <AutoGrowTextarea
        className="draft-input"
        placeholder={home.describePlaceholder}
        value={prompt}
        onChange={setPrompt}
      />
      <button
        className="btn btn-ai"
        onClick={onGenerate}
        disabled={generate.isPending || !prompt.trim()}
      >
        {generate.isPending ? home.drafting : home.generateDraft}
      </button>
    </div>
  );

  return (
    <div className="page">
      <div className="page-head">
        <h1>{home.title}</h1>
        <button className="btn btn-primary" onClick={onCreate} disabled={create.isPending}>
          {create.isPending ? "Creating…" : "New template"}
        </button>
      </div>

      {/* First on the page. Describing a survey and having it drafted is the most
          distinctive thing this product does, and putting it under the work made it the
          least visible. A bar rather than a card: one line that grows as you type, so
          the summary below it stays above the fold. */}
      {draftBar}

      {generate.error ? (
        <div className="error-text">{(generate.error as Error).message}</div>
      ) : null}

      {create.error ? (
        <div className="error-text">{(create.error as Error).message}</div>
      ) : null}

      {totals && audience && audience.surveys > 0 ? (
        <div className="hero-band">
          <div className="hero-head">{home.bandTitle(audience.surveys)}</div>

          {/* Three stages of one journey through one audience, so a single hue getting
              darker as it gets further along rather than three unrelated colours. The
              gaps between segments are the surface showing through, which keeps two
              adjacent shades from reading as one block. */}
          <div
            className="audience-bar"
            role="img"
            aria-label={home.bandAria(
              share(audience.answered),
              share(partWay),
              share(notYet),
            )}
          >
            <span className="seg seg-answered" style={{ inlineSize: `${share(audience.answered)}%` }} />
            <span className="seg seg-partway" style={{ inlineSize: `${share(partWay)}%` }} />
            <span className="seg seg-notyet" style={{ inlineSize: `${share(notYet)}%` }} />
          </div>

          <div className="hero-legend">
            <span className="legend-item">
              <span className="swatch swatch-answered" />
              <b>{share(audience.answered)}%</b> {home.segAnswered}
              <span className="legend-count">{audience.answered}</span>
            </span>
            <span className="legend-item">
              <span className="swatch swatch-partway" />
              <b>{share(partWay)}%</b> {home.segPartWay}
              <span className="legend-count">{partWay}</span>
            </span>
            <span className="legend-item">
              <span className="swatch swatch-notyet" />
              <b>{share(notYet)}%</b> {home.segNotYet}
              <span className="legend-count">{notYet}</span>
            </span>
          </div>

          {/* Said on the page rather than left as a puzzle: reach is summed per survey,
              so a person in two audiences is two of this number. Only shown when it can
              actually be happening. */}
          {audience.surveys > 1 ? (
            <div className="hero-note">{home.countedPerSurvey}</div>
          ) : null}

        </div>
      ) : null}

      {isLoading ? <div className="muted">{common.loading}</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}

      {groups && groups.needsYou.length > 0 ? (
        <>
          <h2 className="section-head">
            {home.groupNeedsYou}
            <span className="section-count">{groups.needsYou.length}</span>
          </h2>
          <div className="template-list">
            {groups.needsYou.map(({ row: r, why: attention }) => (
              <div key={r.id} className="template-row template-row-alert">
                <Link href={landingFor(r)} className="template-row-main">
                  <div className="template-title">{r.title}</div>
                  <div className="template-meta template-why">{why(r, attention)}</div>
                </Link>
                <div className="template-row-actions">
                  {attention === "resultsReady" ? (
                    <Link href={`/templates/${r.id}/report`} className="btn btn-primary">
                      {home.readResults}
                    </Link>
                  ) : (
                    <Link href={`/templates/${r.id}`} className="btn btn-secondary">
                      {home.openBuilder}
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {groups && groups.running.length > 0 ? (
        <>
          <h2 className="section-head">
            {home.groupRunning}
            <span className="section-count">{groups.running.length}</span>
            {groups.needsYou.length === 0 ? (
              <span className="section-note">{home.allRunning}</span>
            ) : null}
          </h2>
          <div className="template-list">
            {groups.running.map((r) => (
              <div key={r.id} className="template-row">
                <Link href={landingFor(r)} className="template-row-main">
                  <div className="template-title">{r.title}</div>
                  <div className="template-meta">
                    {reachLine(r)}
                    {r.in_progress > 0 ? ` · ${r.in_progress} ${home.inProgress}` : ""}
                    {/* Only when the two disagree, which is only on rows written before
                        one answer per person was enforced. It shrinks to nothing on its
                        own rather than being a permanent feature of the page. */}
                    {r.started > r.people_started
                      ? ` · ${home.runsFromPeople(r.started, r.people_started)}`
                      : ""}
                  </div>
                </Link>
                {/* One ratio against a limit, so a meter rather than a number: the bar
                    is comparable down the column at a glance and the figure beside it
                    is the finding. */}
                <div className="reach-meter" title={reachLine(r)}>
                  <span className="reach-track">
                    <span
                      className="reach-fill"
                      style={{
                        inlineSize: `${Math.min(100, Math.round((r.response_rate ?? 0) * 100))}%`,
                      }}
                    />
                  </span>
                  <span className="reach-figure">
                    {r.response_rate === null ? "-" : `${Math.round(r.response_rate * 100)}%`}
                  </span>
                </div>
                <div className="template-row-actions">
                  {r.completed > 0 ? (
                    <Link href={`/templates/${r.id}/report`} className="btn btn-secondary">
                      {home.report}
                    </Link>
                  ) : null}
                  <button
                    className="btn btn-quiet"
                    onClick={() => close.mutate(r.id)}
                    disabled={close.isPending}
                  >
                    {close.isPending && close.variables === r.id ? home.closing : home.closeSurvey}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {groups && groups.closed.length > 0 ? (
        <>
          <h2 className="section-head">
            {home.groupClosed}
            <span className="section-count">{groups.closed.length}</span>
          </h2>
          <div className="template-list">
            {groups.closed.map((r) => (
              <div key={r.id} className="template-row template-row-quiet">
                <Link href={landingFor(r)} className="template-row-main">
                  <div className="template-title">{r.title}</div>
                  <div className="template-meta">{reachLine(r)}</div>
                </Link>
                <div className="template-row-actions">
                  {r.completed > 0 ? (
                    <Link href={`/templates/${r.id}/report`} className="btn btn-secondary">
                      {home.report}
                    </Link>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {rows && rows.length === 0 ? <div className="muted">{home.empty}</div> : null}


    </div>
  );
}
