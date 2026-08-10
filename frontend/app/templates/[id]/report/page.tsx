"use client";

import Link from "next/link";
import { use } from "react";

import { useReport, useSummariseSurvey } from "@/lib/queries";
import { useT } from "@/lib/i18n/useT";
import { useUserStore } from "@/lib/store";
import type { QuestionReport, SurveySummary } from "@/lib/types";

/** The tally, as bars in the author's option order.
 *
 *  Widths are a share of the largest count rather than of the number who answered, so a
 *  question where nobody agreed still reads as a shape. The number is always printed
 *  beside the bar: a bar is for comparing at a glance, and the count is the finding.
 */
function Bars({ question }: { question: QuestionReport }) {
  const msg = useT();
  const most = Math.max(1, ...question.counts.map((c) => c.count));
  return (
    <ul className="bars">
      {question.counts.map((c) => (
        <li key={`${c.label}-${c.write_in}`}>
          <span className="bar-label">
            {c.label}
            {c.write_in ? <span className="muted"> {msg.report.writeIn}</span> : null}
          </span>
          <span className="bar-track">
            <span className="bar-fill" style={{ inlineSize: `${(c.count / most) * 100}%` }} />
          </span>
          <span className="bar-count">{c.count}</span>
        </li>
      ))}
    </ul>
  );
}


/** The whole-survey recap.
 *
 *  Every figure here is read out of the report, never out of the model: a finding is
 *  prose with no digits in it (the API refuses one that has any) and the tally beside it
 *  is the question's own. So the words can be arguable and the numbers cannot be wrong.
 */
function Recap({ recap }: { recap: SurveySummary }) {
  const msg = useT();
  return (
    <div className="card recap">
      <div className="card-label">{msg.report.recapFrom(recap.runs_included, recap.version)}</div>
      <h2 className="recap-headline">{recap.headline}</h2>

      <ul className="recap-findings">
        {recap.findings.map((f, i) => (
          <li key={i}>
            <span className="recap-statement">{f.statement}</span>
            {f.question_text ? (
              <span className="muted recap-source">
                {" "}
                {msg.report.fromQuestion((f.question_position ?? 0) + 1, f.question_text)}
              </span>
            ) : null}
            {f.counts.length > 0 ? (
              <span className="recap-counts">
                {f.counts
                  .filter((c) => c.count > 0)
                  .map((c) => `${c.label} ${c.count}`)
                  .join(" · ")}
                {f.average !== null ? ` · ${msg.report.average(f.average.toFixed(1))}` : ""}
              </span>
            ) : null}
          </li>
        ))}
      </ul>

      {recap.notable_quotes.length > 0 ? (
        <div className="recap-quotes">
          {recap.notable_quotes.map((q, i) => (
            <blockquote key={i}>
              {q.quote}
              <cite>
                {q.respondent} · {q.question}
              </cite>
            </blockquote>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const msg = useT();
  const { id } = use(params);
  const currentUserId = useUserStore((s) => s.currentUserId);
  const { data: report, isLoading, error } = useReport(id);
  const recap = useSummariseSurvey(id);

  if (!currentUserId) return <div className="empty">{msg.builder.pickUser}</div>;
  if (isLoading) return <div className="muted">{msg.common.loading}</div>;
  if (error || !report) {
    return (
      <div className="error-text">{error ? (error as Error).message : msg.common.notFound}</div>
    );
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>{report.title}</h1>
        <div className="page-head-actions">
          <Link href={`/templates/${id}/results`} className="btn btn-secondary">
            {msg.report.everyAnswer}
          </Link>
          <Link href={`/templates/${id}`} className="btn btn-secondary">
            {msg.report.edit}
          </Link>
        </div>
      </div>

      <div className="stat-row">
        <div className="stat">
          <div className="stat-value">
            {report.reach > 0
              ? `${report.people_completed}/${report.reach}`
              : report.people_completed}
          </div>
          <div className="stat-label">{msg.report.responded}</div>
        </div>
        <div className="stat">
          <div className="stat-value">{report.runs_total}</div>
          <div className="stat-label">{msg.report.responses}</div>
        </div>
        <div className="stat">
          <div className="stat-value">v{report.version}</div>
          <div className="stat-label">{msg.report.version}</div>
        </div>
      </div>

      {/* Said on the page rather than left in the code: those runs answered different
          questions under different ids, so counting them here would change what every
          number means. */}
      {report.runs_on_earlier_versions > 0 ? (
        <div className="notice">{msg.report.earlierVersions(report.runs_on_earlier_versions)}</div>
      ) : null}

      {/* Only when the two disagree, which is only on answers given before one answer
          per person was enforced. Said here rather than left as a discrepancy between
          two numbers on the same page. */}
      {report.runs_total > report.people_started ? (
        <div className="notice">
          {msg.report.moreRunsThanPeople(report.runs_total, report.people_started)}
        </div>
      ) : null}

      {report.runs_total === 0 ? <div className="muted">{msg.report.nobodyYet}</div> : null}

      {/* Author-triggered, never on render: it costs model calls and can fail, and the
          numbers below must load either way. */}
      {report.runs_completed > 0 ? (
        <div className="recap-block">
          {recap.data ? <Recap recap={recap.data} /> : null}
          <div className="recap-actions">
            <button
              className="btn btn-secondary"
              onClick={() => recap.mutate(Boolean(recap.data))}
              disabled={recap.isPending}
            >
              {recap.isPending
                ? msg.report.recapWorking
                : recap.data
                  ? msg.report.recapAgain
                  : msg.report.recapAsk}
            </button>
            {recap.error ? (
              <span className="error-text">{(recap.error as Error).message}</span>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="questions">
        {report.questions.map((q, i) => (
          <div className="card" key={q.id}>
            <div className="card-label">{msg.builder.questionLabel(i + 1)}</div>
            <h2 className="report-question">{q.text}</h2>
            <p className="muted report-meta">
              {msg.report.answeredBy(q.answered)}
              {q.declined > 0 ? ` · ${msg.report.declinedBy(q.declined)}` : ""}
              {q.average !== null ? ` · ${msg.report.average(q.average.toFixed(1))}` : ""}
              {q.probed > 0 ? ` · ${msg.report.probedBy(q.probed)}` : ""}
            </p>

            {q.counts.length > 0 ? <Bars question={q} /> : null}

            {/* Counted here, read on click. Forty open answers is a long list to scroll
                past on the way to the next question, and grouping them would mean the
                model deciding what people meant, which these numbers are not. */}
            {q.verbatim.length > 0 ? (
              <details className="verbatim">
                <summary className="muted">{msg.report.inTheirWords(q.verbatim.length)}</summary>
                <ul>
                  {q.verbatim.map((v, j) => (
                    <li key={j}>{v}</li>
                  ))}
                </ul>
              </details>
            ) : null}

            {/* Its own list, below the answers rather than mixed into them. A follow-up
                answers a question the model wrote, so presenting it as an answer to this
                one would credit the author's question with words it never asked for. */}
            {q.follow_ups.length > 0 ? (
              <details className="verbatim">
                <summary className="muted">{msg.report.whatProbesFound(q.follow_ups.length)}</summary>
                <ul>
                  {q.follow_ups.map((v, j) => (
                    <li key={j}>{v}</li>
                  ))}
                </ul>
              </details>
            ) : null}

            {q.counts.length === 0 && q.verbatim.length === 0 && q.follow_ups.length === 0 ? (
              <p className="muted">{msg.report.noAnswers}</p>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
