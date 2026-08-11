"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { SurveyNav } from "@/components/SurveyNav";
import { Transcript } from "@/components/Transcript";
import { useT } from "@/lib/i18n/useT";
import {
  useCurrentUser,
  useSummariseRun,
  useTemplate,
  useTemplateRun,
  useTemplateRuns,
} from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import type { RunAnswer, RunDetail } from "@/lib/types";

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

function totalProbes(run: RunDetail): number {
  return Object.values(run.follow_ups_asked ?? {}).reduce((sum, n) => sum + n, 0);
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

/** The AI summary panel. Only offered on a completed run: summarising a half-finished
 *  one would describe a response the respondent is still giving. */
function SummaryCard({ templateId, run }: { templateId: string; run: RunDetail }) {
  const msg = useT();
  const summarise = useSummariseRun(templateId, run.id);
  const summary = run.summary;
  const done = run.status === "completed";

  return (
    <div className="card">
      <div className="card-label">
        {msg.results.summary}
        <span className="chip chip-follow">AI</span>
      </div>

      {summary ? (
        <div className="summary">
          <p className="summary-headline">{summary.headline}</p>
          {summary.key_facts.length > 0 ? (
            <ul className="summary-facts">
              {summary.key_facts.map((fact, i) => (
                <li key={i}>{fact}</li>
              ))}
            </ul>
          ) : null}
          {summary.notable_quotes.length > 0 ? (
            <div className="summary-quotes">
              {summary.notable_quotes.map((q, i) => (
                <blockquote key={i} className="summary-quote">
                  “{q.quote}”<cite>{q.question}</cite>
                </blockquote>
              ))}
            </div>
          ) : null}
          <div className="answer-stamp">
            {summary.generated_at
              ? `Generated ${new Date(summary.generated_at).toLocaleString()}`
              : "Generated"}
            {summary.prompt_version ? ` · ${summary.prompt_version}` : ""}
          </div>
        </div>
      ) : (
        <div className="muted">
          {done
            ? "No summary yet."
            : "Available once the respondent finishes — a partial run would summarise an answer still being given."}
        </div>
      )}

      {summarise.error ? (
        <div className="error-text">{(summarise.error as Error).message}</div>
      ) : null}

      <div className="page-head-actions">
        <button
          className="btn btn-secondary"
          onClick={() => summarise.mutate(Boolean(summary))}
          disabled={!done || summarise.isPending}
          title={
            done
              ? "Ask the model for the key facts and notable quotes in this response"
              : "Only a completed run can be summarised"
          }
        >
          {summarise.isPending
            ? "Summarising…"
            : summary
              ? "Regenerate summary"
              : "Generate summary"}
        </button>
      </div>
    </div>
  );
}

export default function ResultsPage() {
  const msg = useT();
  const { id } = useParams<{ id: string }>();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: runs, isLoading, error } = useTemplateRuns(id);
  // For the heading only: this page showed the word "Responses" and never which
  // survey's responses they were.
  const { data: template } = useTemplate(id);
  const [selected, setSelected] = useState<string | null>(null);
  const detail = useTemplateRun(id, selected);
  const router = useRouter();

  const isRespondent = currentUser?.role === "respondent";
  useEffect(() => {
    if (isRespondent) router.replace("/respond");
  }, [isRespondent, router]);

  if (!currentUserId) {
    return <div className="empty">{msg.results.pickAuthor}</div>;
  }
  if (isRespondent) {
    return <div className="empty">{msg.home.goingToRespond}</div>;
  }

  return (
    <div className="page">
      <SurveyNav templateId={id} current="responses" />
      <div className="page-head">
        {/* The survey's own title, not the word "Responses". This page never said which
            survey you were reading, which is half of not knowing where you are. */}
        <h1>{template?.title ?? msg.results.title}</h1>
      </div>

      {isLoading ? <div className="muted">{msg.common.loading}</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}
      {runs && runs.length === 0 ? (
        <div className="muted">{msg.results.empty}</div>
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
              <div className="muted">{msg.results.pickOne}</div>
            ) : detail.isLoading ? (
              <div className="muted">{msg.common.loading}</div>
            ) : detail.error ? (
              <div className="error-text">{(detail.error as Error).message}</div>
            ) : detail.data ? (
              <>
                <SummaryCard templateId={id} run={detail.data} />

                <div className="card">
                  <div className="card-label">{msg.results.answers}</div>
                  <div className="detail-head">
                    <strong>{detail.data.respondent_name}</strong>
                    <span>version {detail.data.version}</span>
                    <span>
                      started {new Date(detail.data.started_at).toLocaleString()}
                      {detail.data.completed_at
                        ? `, completed ${new Date(detail.data.completed_at).toLocaleString()}`
                        : ", still in progress"}
                    </span>
                    {/* Run-level total as well as the per-question chips: a question that
                        was probed but never answered has no row to hang a chip on. */}
                    {totalProbes(detail.data) > 0 ? (
                      <span>
                        {totalProbes(detail.data)} {msg.results.followUp}
                        {totalProbes(detail.data) === 1 ? "" : "s"} asked
                      </span>
                    ) : null}
                  </div>
                  <div className="answer-list">
                    {groupByQuestion(detail.data.answers).map((group) => (
                      <div key={group.questionId} className="answer">
                        <div className="answer-q">
                          {group.scripted?.question_text ?? "Unanswered question"}
                          {detail.data.follow_ups_asked?.[group.questionId] ? (
                            <span
                              className="chip chip-follow"
                              title={msg.results.probeHint}
                            >
                              {detail.data.follow_ups_asked[group.questionId]} probed
                            </span>
                          ) : null}
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
                          <div className="muted">{msg.results.notAnswered}</div>
                        )}
                        {group.followUps.map((followUp, i) => (
                          <div key={`${group.questionId}-${i}`} className="answer-follow">
                            <div className="answer-q">
                              {followUp.question_text}
                              <span className="chip chip-follow">{msg.results.followUp}</span>
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
                      <div className="muted">{msg.results.nothingAnswered}</div>
                    ) : null}
                  </div>
                </div>

                <div className="card">
                  <div className="card-label">{msg.results.transcript}</div>
                  <Transcript messages={detail.data.messages} flat />
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
