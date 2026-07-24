"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useCurrentUser, useTemplateRun, useTemplateRuns } from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import type { RunAnswer } from "@/lib/types";

interface AnswerGroup {
  questionId: string;
  scripted: RunAnswer | null;
  followUps: RunAnswer[];
}

/** Follow-ups carry the question id of the question they probed, so they group under it. */
function groupByQuestion(answers: RunAnswer[]): AnswerGroup[] {
  const groups: AnswerGroup[] = [];
  for (const answer of answers) {
    let group = groups.find((g) => g.questionId === answer.question_id);
    if (!group) {
      group = { questionId: answer.question_id, scripted: null, followUps: [] };
      groups.push(group);
    }
    if (answer.kind === "scripted") group.scripted = answer;
    else group.followUps.push(answer);
  }
  return groups;
}

function stamp(answer: RunAnswer, respondent: string, version: number): string {
  const when = new Date(answer.answered_at).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
  return `${respondent} · ${when} · v${version}`;
}

/** Answers are stored shaped per answer type, so read whichever key is present. */
function readValue(value: Record<string, unknown>): string {
  if ("text" in value) return String(value.text);
  if ("rating" in value) return `${value.rating} out of 5`;
  if ("number" in value) return String(value.number);
  if ("date" in value) return String(value.date);
  if ("yes_no" in value) return value.yes_no ? "Yes" : "No";
  if ("option" in value) return String(value.option);
  if ("options" in value) {
    const chosen = (value.options as string[]).join(", ");
    const other = value.other ? ` (+ ${(value.other as string[]).join(", ")})` : "";
    return chosen + other;
  }
  if ("other" in value) return String(value.other);
  if ("unanswerable" in value) return `Declined — ${value.unanswerable}`;
  return JSON.stringify(value);
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: runs, isLoading, error } = useTemplateRuns(id);
  const [selected, setSelected] = useState<string | null>(null);
  const detail = useTemplateRun(id, selected);
  const router = useRouter();

  const isRespondent = currentUser?.role === "respondent";
  useEffect(() => {
    if (isRespondent) router.replace("/respond");
  }, [isRespondent, router]);

  if (!currentUserId) {
    return <div className="empty">Pick an author in the top bar to see responses.</div>;
  }
  if (isRespondent) {
    return <div className="empty">Taking you to Respond…</div>;
  }

  async function download(format: "csv" | "json") {
    const res = await api.exportRuns(id, format);
    const blob = await res.blob();
    // The backend names the file after the survey; fall back if the header is absent.
    const disposition = res.headers.get("Content-Disposition") ?? "";
    const name = /filename="([^"]+)"/.exec(disposition)?.[1] ?? `responses.${format}`;
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = name;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>Responses</h1>
        <div className="page-head-actions">
          <button
            className="btn btn-secondary"
            onClick={() => download("csv")}
            disabled={!runs || runs.length === 0}
            title="Every answer as a spreadsheet row — opens directly in Excel"
          >
            Export CSV
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => download("json")}
            disabled={!runs || runs.length === 0}
            title="Every answer as structured JSON"
          >
            Export JSON
          </button>
          <Link href={`/templates/${id}`} className="btn btn-secondary">
            Back to builder
          </Link>
        </div>
      </div>

      {isLoading ? <div className="muted">Loading…</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}
      {runs && runs.length === 0 ? (
        <div className="muted">No responses yet. Publish the survey and answer it to see it here.</div>
      ) : null}

      {runs && runs.length > 0 ? (
        <div className="results">
          <div className="results-list">
            {runs.map((run) => (
              <button
                key={run.id}
                className={run.id === selected ? "result-row result-row-on" : "result-row"}
                onClick={() => setSelected(run.id)}
              >
                <div className="result-name">{run.respondent_name}</div>
                <div className="result-meta">
                  {run.answered} of {run.total} · v{run.version}
                </div>
                <span className={`pill pill-${run.status === "completed" ? "published" : "draft"}`}>
                  {run.status === "completed" ? "complete" : "in progress"}
                </span>
              </button>
            ))}
          </div>

          <div className="results-detail">
            {!selected ? (
              <div className="muted">Pick a response to read it.</div>
            ) : detail.isLoading ? (
              <div className="muted">Loading…</div>
            ) : detail.error ? (
              <div className="error-text">{(detail.error as Error).message}</div>
            ) : detail.data ? (
              <>
                <div className="card">
                  <div className="card-label">Answers</div>
                  <div className="detail-head">
                    <strong>{detail.data.respondent_name}</strong>
                    <span>version {detail.data.version}</span>
                    <span>
                      started {new Date(detail.data.started_at).toLocaleString()}
                      {detail.data.completed_at
                        ? `, completed ${new Date(detail.data.completed_at).toLocaleString()}`
                        : ", still in progress"}
                    </span>
                  </div>
                  <div className="answer-list">
                    {groupByQuestion(detail.data.answers).map((group) => (
                      <div key={group.questionId} className="answer">
                        <div className="answer-q">
                          {group.scripted?.question_text ?? "Unanswered question"}
                        </div>
                        {group.scripted ? (
                          <>
                            <div className="answer-v">{readValue(group.scripted.value)}</div>
                            <div className="answer-stamp">
                              {stamp(
                                group.scripted,
                                detail.data.respondent_name,
                                detail.data.version,
                              )}
                            </div>
                          </>
                        ) : (
                          <div className="muted">Not answered</div>
                        )}
                        {group.followUps.map((followUp, i) => (
                          <div key={`${group.questionId}-${i}`} className="answer-follow">
                            <div className="answer-q">
                              {followUp.question_text}
                              <span className="chip chip-follow">follow-up</span>
                            </div>
                            <div className="answer-v">{readValue(followUp.value)}</div>
                            <div className="answer-stamp">
                              {stamp(followUp, detail.data.respondent_name, detail.data.version)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ))}
                    {detail.data.answers.length === 0 ? (
                      <div className="muted">Nothing answered yet.</div>
                    ) : null}
                  </div>
                </div>

                <div className="card">
                  <div className="card-label">Transcript</div>
                  <div className="chat-thread chat-thread-flat">
                    {detail.data.messages.map((message, i) => (
                      <div
                        key={`${message.created_at}-${i}`}
                        className={`bubble bubble-${message.role}`}
                      >
                        {message.content}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
