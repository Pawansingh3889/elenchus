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
import { useT } from "@/lib/i18n/useT";
import { useDraftNoteStore, useUserStore } from "@/lib/store";

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
    // A blank survey restricts nothing and is aimed nowhere in particular until its
    // author says so, which is what the respondent pool means.
    const t = await create.mutateAsync({
      title: "Untitled survey",
      audience: "respondents",
      allowed_answer_types: [],
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

  // Totals across every survey this author owns, from the rows already fetched. The
  // per-survey numbers were always here; what was missing was the one line that says
  // how the whole thing is going, which is the question this page is opened to answer.
  const totals = rows
    ? {
        surveys: rows.length,
        published: rows.filter((r) => r.status === "published").length,
        started: rows.reduce((n, r) => n + r.started, 0),
        completed: rows.reduce((n, r) => n + r.completed, 0),
      }
    : null;
  // Null rather than 0 when nobody has started, the same honesty the row applies:
  // 0% reads as everyone abandoning, which is a different thing from nobody arriving.
  const completion =
    totals && totals.started > 0 ? Math.round((totals.completed / totals.started) * 100) : null;

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
          <div className="stat">
            <div className="stat-value">{totals.surveys}</div>
            <div className="stat-label">{home.statSurveys}</div>
          </div>
          <div className="stat">
            <div className="stat-value">{totals.published}</div>
            <div className="stat-label">{home.statPublished}</div>
          </div>
          <div className="stat">
            <div className="stat-value">{totals.started}</div>
            <div className="stat-label">{home.statResponses}</div>
          </div>
          <div className="stat">
            {/* A plain hyphen, not a zero: nobody has started, so there is no rate yet. */}
            <div className="stat-value">{completion === null ? "-" : `${completion}%`}</div>
            <div className="stat-label">{home.statCompletion}</div>
          </div>
        </div>
      ) : null}

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

      <h2 className="section-head">{home.yourSurveys}</h2>

      {isLoading ? <div className="muted">{common.loading}</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}

      <div className="template-list">
        {rows?.map((r) => (
          <div key={r.id} className="template-row">
            <Link href={`/templates/${r.id}`} className="template-row-main">
              <div className="template-title">{r.title}</div>
              <div className="template-meta">
                {r.started === 0 ? (
                  home.noResponses
                ) : (
                  <>
                    {r.started} {home.started}
                    {" · "}
                    {r.completed} {home.completedLabel}
                    {r.in_progress > 0 ? ` · ${r.in_progress} ${home.inProgress}` : ""}
                    {r.completion_rate !== null
                      ? ` · ${Math.round(r.completion_rate * 100)}%`
                      : ""}
                  </>
                )}
              </div>
            </Link>
            <div className="template-row-actions">
              <span className={`pill pill-${r.status}`}>{r.status}</span>
              {/* Only a published survey can be closed, which is the same rule the
                  service enforces. Offering it on a draft would be offering a 409. */}
              {r.status === "published" ? (
                <button
                  className="btn btn-secondary"
                  onClick={() => close.mutate(r.id)}
                  disabled={close.isPending}
                >
                  {close.isPending && close.variables === r.id
                    ? home.closing
                    : home.closeSurvey}
                </button>
              ) : null}
            </div>
          </div>
        ))}
        {rows && rows.length === 0 ? <div className="muted">{home.empty}</div> : null}
      </div>
    </div>
  );
}
