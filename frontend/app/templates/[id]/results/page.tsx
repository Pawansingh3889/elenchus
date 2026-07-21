"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { useTemplateRun, useTemplateRuns } from "@/lib/queries";
import { useUserStore } from "@/lib/store";

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
  const { data: runs, isLoading, error } = useTemplateRuns(id);
  const [selected, setSelected] = useState<string | null>(null);
  const detail = useTemplateRun(id, selected);

  if (!currentUserId) {
    return <div className="empty">Pick an author in the top bar to see responses.</div>;
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>Responses</h1>
        <Link href={`/templates/${id}`} className="btn btn-secondary">
          Back to builder
        </Link>
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
                  <div className="answer-list">
                    {detail.data.answers.map((answer, i) => (
                      <div key={`${answer.question_id}-${i}`} className="answer">
                        <div className="answer-q">
                          {answer.question_text}
                          {answer.kind === "follow_up" ? (
                            <span className="chip chip-follow">follow-up</span>
                          ) : null}
                        </div>
                        <div className="answer-v">{readValue(answer.value)}</div>
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
