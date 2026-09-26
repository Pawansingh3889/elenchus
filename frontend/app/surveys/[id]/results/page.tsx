"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { demo, exportAnswers } from "@/lib/demo";
import { useSession } from "@/lib/queries";

export default function SurveyResults() {
  const { id } = useParams<{ id: string }>();
  const { data: session } = useSession();
  const qc = useQueryClient();
  const [status, setStatus] = useState("all");
  const [question, setQuestion] = useState("all");
  const [selectedRun, setSelectedRun] = useState("");
  const report = useQuery({ queryKey: ["report", id, session?.id], queryFn: () => demo.report(id), enabled: !!session });
  const matrix = useQuery({ queryKey: ["matrix", id, session?.id], queryFn: () => demo.matrix(id), enabled: !!session });
  const stored = useQuery({ queryKey: ["recap", id, session?.id], queryFn: () => demo.storedRecap(id), enabled: !!session });
  const access = useQuery({ queryKey: ["access", session?.id], queryFn: demo.access, enabled: !!session });
  const transcript = useQuery({ queryKey: ["transcript", id, selectedRun, session?.id], queryFn: () => demo.run(id, selectedRun), enabled: !!session && !!selectedRun });
  const summarise = useMutation({ mutationFn: () => demo.summarise(id), onSuccess: recap => qc.setQueryData(["recap", id, session?.id], { recap, absence: null }) });
  const refresh = () => { for (const key of ["report", "matrix", "recap"]) void qc.invalidateQueries({ queryKey: [key, id] }); };
  if (!session) return <div className="product-page"><Link href="/demo">Enter your workspace</Link> to read these results.</div>;
  const data = report.data;
  const runs = matrix.data?.runs ?? [];
  const durations = runs.filter(run => run.status === "completed" && run.completed_at).map(run => (new Date(run.completed_at!).getTime() - new Date(run.started_at).getTime()) / 60000).sort((a, b) => a - b);
  const middle = Math.floor(durations.length / 2);
  const median = durations.length ? (durations.length % 2 ? durations[middle] : (durations[middle - 1] + durations[middle]) / 2) : null;
  const recap = stored.data?.recap;
  return <div className="product-page report-print">
    <header className="page-heading"><div><Link className="no-print" href={`/surveys/${id}`}>← Manage survey</Link><p className="eyebrow">FROM RESPONSES TO UNDERSTANDING</p><h1>{data?.title ?? "Survey results"}</h1><p>Results from stored responses, including unfinished conversations.</p></div><div className="action-row no-print"><button className="btn" onClick={refresh} disabled={report.isFetching}>Refresh</button><button className="btn" disabled={!matrix.data} onClick={() => matrix.data && exportAnswers(matrix.data)}>Export CSV</button><button className="btn btn-primary" disabled={!data} onClick={() => window.print()}>Print / save PDF</button></div></header>
    {(report.error || matrix.error || access.error) && <p role="alert">{(report.error || matrix.error || access.error)?.message}</p>}
    {report.isPending && <p role="status">Loading results…</p>}
    {data && <>
      <div className="metric-grid"><article><span>Started</span><strong>{data.runs_total}</strong><small>Stored respondent sessions</small></article><article><span>Completed</span><strong>{data.runs_completed}</strong><small>{data.runs_total - data.runs_completed} unfinished</small></article><article><span>Completion</span><strong>{data.runs_total ? `${Math.round(100 * data.runs_completed / data.runs_total)}%` : "No data"}</strong><small>Completed / started</small></article><article><span>Median elapsed time</span><strong>{median === null ? "No data" : `${median.toFixed(1)} min`}</strong><small>{durations.length} completed sessions; includes pauses</small></article></div>
      <p className="metric-note">Invitation reach is unknown for shared links, so an invitation response rate is not shown. One browser session is not proof of one unique person. Withdrawn and expired responses are excluded from these results.</p>
      <section className="product-card summary-card"><div className="page-heading"><div><p className="eyebrow">READ THE PATTERNS</p><h2>Survey summary</h2></div><button className="btn btn-primary no-print" disabled={summarise.isPending || !access.data?.active || !data.runs_completed || !!recap} onClick={() => summarise.mutate()}>{summarise.isPending ? "Writing and checking…" : recap ? "Summary up to date" : "Generate a checked summary"}</button></div>
        {stored.data?.absence === "outdated" && <p className="notice">Responses changed since the last summary. Generate a fresh one to use the current evidence.</p>}
        {(stored.error || summarise.error) && <p role="alert">{(stored.error || summarise.error)?.message}</p>}
        {!recap && <p>{data.runs_completed ? "Generate a summary when you are ready. This uses the AI allowance; opening this page does not." : "A summary becomes available after the first completed response."}</p>}
        {recap && <><h3 className="summary-headline">{recap.headline}</h3><p>{recap.runs_included} completed sessions when generated · {new Date(recap.generated_at).toLocaleString()}</p><div className="summary-columns">{[{ title: "What the responses show", items: recap.findings }, { title: "What respondents suggested", items: recap.suggestions }].map(group => <div key={group.title}><h3>{group.title}</h3>{group.items.length ? group.items.map((item, i) => <article className="finding" key={i}><p>{item.statement}</p>{item.question_position !== null ? <a href={`#question-${item.question_position}`} onClick={() => setQuestion("all")}>Read source question {item.question_position + 1} and its answers →</a> : <a href="#question-results" onClick={() => setQuestion("all")}>Read all source questions →</a>}{item.answered !== null && <small>{item.answered} usable answers to the source question</small>}</article>) : <p>No supported items recorded.</p>}</div>)}</div><div className="notice"><h3>AI-proposed actions, for human review</h3><p>These are suggestions from the model. They are not respondent quotes or agreed commitments.</p>{recap.proposed_actions.length ? <ul>{recap.proposed_actions.map((action, i) => <li key={i}>{action.action}{action.question_position !== null && <> <a href={`#question-${action.question_position}`} onClick={() => setQuestion("all")}>Related question {action.question_position + 1}</a></>}</li>)}</ul> : <p>No AI actions proposed.</p>}</div><p className="muted">A separate AI review checks the factual summary. It can still be wrong. Read the source answers before acting; small samples describe these respondents only.</p></>}
      </section>
      <section id="question-results"><div className="page-heading"><h2>Question by question</h2><label className="no-print">View <select value={question} onChange={event => setQuestion(event.target.value)}><option value="all">All questions</option>{data.questions.map(item => <option key={item.id} value={item.id}>Q{item.position + 1}: {item.text}</option>)}</select></label></div>
        {data.questions.map(item => <article id={`question-${item.position}`} key={item.id} className={`product-card question-result ${question !== "all" && question !== item.id ? "screen-hidden" : ""}`}><p className="eyebrow">QUESTION {item.position + 1}</p><h3>{item.text}</h3><p>{item.answered} usable answers · {item.declined} declined{item.average !== null && <> · Average {item.average.toFixed(2)}{item.unit ? ` ${item.unit}` : ""}</>}</p>{item.low !== null && <p>Range: {item.low} to {item.high}{item.unit ? ` ${item.unit}` : ""}</p>}
          {item.counts.length > 0 && <><div className="result-bars" aria-hidden="true">{item.counts.map(option => <div key={`${option.label}-${option.write_in}`}><span>{option.label}</span><meter min={0} max={Math.max(1, item.answered)} value={option.count} /><strong>{option.count}</strong></div>)}</div><table><caption>Counts from recorded answers. {item.answer_type === "multi_select" ? "People could select more than one option." : "One answer per session."}</caption><thead><tr><th>Answer</th><th>Count</th><th>Share of usable answers</th></tr></thead><tbody>{item.counts.map(option => <tr key={`${option.label}-${option.write_in}`}><td>{option.label}{option.write_in ? " (written alternative)" : ""}</td><td>{option.count}</td><td>{item.answered ? `${(100 * option.count / item.answered).toFixed(0)}%` : "No data"}</td></tr>)}</tbody></table></>}
          {!!item.verbatim.length && <details className="source-answers"><summary>Read {item.verbatim.length} recorded written answers</summary>{item.verbatim.map((text, i) => <blockquote key={i}>{text}</blockquote>)}</details>}
          {!!item.follow_ups.length && <details className="source-answers"><summary>Read {item.follow_ups.length} follow-up answers from {item.probed} sessions</summary><p>These are kept separate from the original question&apos;s tally.</p>{item.follow_ups.map((text, i) => <blockquote key={i}>{text}</blockquote>)}</details>}
          {!item.answered && !item.declined && <p>No recorded answers yet.</p>}
        </article>)}
      </section>
      <section className="product-card"><div className="page-heading"><h2>Conversations</h2><label className="no-print">Status <select value={status} onChange={event => setStatus(event.target.value)}><option value="all">All</option><option value="completed">Completed</option><option value="in_progress">In progress</option><option value="abandoned">Finished early</option></select></label></div><p>Labels identify sessions within this survey, not named people. This filter changes only the conversation list.</p><div className="table-scroll"><table><thead><tr><th>Session</th><th>Status</th><th>Recorded answers</th><th>Started</th><th className="no-print">Read</th></tr></thead><tbody>{runs.filter(run => status === "all" || run.status === status).map(run => <tr key={run.run_id}><td>{run.respondent_label}</td><td>{run.status.replaceAll("_", " ")}</td><td>{new Set(run.answers.filter(answer => answer.kind === "scripted").map(answer => answer.question_id)).size}</td><td>{new Date(run.started_at).toLocaleString()}</td><td className="no-print"><button className="btn" onClick={() => setSelectedRun(run.run_id)}>Read conversation</button></td></tr>)}</tbody></table></div></section>
      {selectedRun && <section className="product-card no-print" aria-live="polite"><div className="page-heading"><h2>{transcript.data?.respondent_label ?? "Conversation"}</h2><button className="btn" onClick={() => setSelectedRun("")}>Close conversation</button></div>{transcript.isFetching && <p>Loading…</p>}{transcript.error && <p role="alert">{transcript.error.message}</p>}{transcript.data?.messages.map((message, i) => <blockquote className={`transcript-${message.role}`} key={i}><strong>{message.role === "user" ? "Participant" : "Interviewer"}</strong><p>{message.content}</p></blockquote>)}</section>}
    </>}
  </div>;
}
