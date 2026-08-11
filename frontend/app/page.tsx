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
import { groupForDashboard, type Attention } from "@/lib/dashboardAttention";
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

  const draftCard = (
        <div className="card generate-card">
          <div className="card-label">{home.draftWithAi}</div>
          <textarea
            placeholder={home.describePlaceholder}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <div className="generate-actions">
            <button
              className="btn btn-ai"
              onClick={onGenerate}
              disabled={generate.isPending || !prompt.trim()}
            >
              {generate.isPending ? "Drafting…" : "✦ Generate draft"}
            </button>
          </div>
          {generate.error ? (
            <div className="error-text">{(generate.error as Error).message}</div>
          ) : null}
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

      {create.error ? (
        <div className="error-text">{(create.error as Error).message}</div>
      ) : null}

      {totals ? (
        <div className="stat-row">
          {/* Accented only when there is something to do, so the number is a signal
              rather than a permanent decoration. */}
          <div className={totals.needsYou > 0 ? "stat stat-alert" : "stat"}>
            <div className="stat-value">{totals.needsYou}</div>
            <div className="stat-label">{home.statNeedsYou}</div>
          </div>
          <div className="stat">
            <div className="stat-value">{totals.running}</div>
            <div className="stat-label">{home.statRunning}</div>
          </div>
          <div className="stat">
            <div className="stat-value">{totals.responses}</div>
            <div className="stat-label">{home.statResponses}</div>
          </div>
        </div>
      ) : null}

      {isLoading ? <div className="muted">{common.loading}</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}

      {groups && groups.needsYou.length > 0 ? (
        <>
          <h2 className="section-head">{home.groupNeedsYou}</h2>
          <div className="template-list">
            {groups.needsYou.map(({ row: r, why: attention }) => (
              <div key={r.id} className="template-row template-row-alert">
                <Link href={`/templates/${r.id}`} className="template-row-main">
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
            {groups.needsYou.length === 0 ? (
              <span className="section-note">{home.allRunning}</span>
            ) : null}
          </h2>
          <div className="template-list">
            {groups.running.map((r) => (
              <div key={r.id} className="template-row">
                <Link href={`/templates/${r.id}`} className="template-row-main">
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
          <h2 className="section-head">{home.groupClosed}</h2>
          <div className="template-list">
            {groups.closed.map((r) => (
              <div key={r.id} className="template-row template-row-quiet">
                <Link href={`/templates/${r.id}`} className="template-row-main">
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

      {/* Last, under the work, because this page is opened to find out what needs doing
          and a creation panel above the list pushed that below it. It needs no special
          case for a new author: with no surveys the groups above render nothing, so this
          is already the first thing on the page. */}
      {draftCard}

    </div>
  );
}
