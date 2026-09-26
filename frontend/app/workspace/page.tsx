"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { demo, blankQuestion } from "@/lib/demo";
import { useSession, useMe } from "@/lib/queries";

export default function Workspace() {
  const { data: session, isPending } = useSession();
  const { data: me } = useMe();
  const router = useRouter();
  const qc = useQueryClient();
  const [prompt, setPrompt] = useState("Create five questions about employee wellbeing, handovers and the support people need on their shift.");
  const [filter, setFilter] = useState("all");
  const access = useQuery({ queryKey: ["access", session?.id], queryFn: demo.access, enabled: !!session });
  const surveys = useQuery({ queryKey: ["dashboard", session?.id], queryFn: demo.dashboard, enabled: !!me?.may_author });
  const created = (id: string) => { void qc.invalidateQueries({ queryKey: ["access"] }); router.push(`/surveys/${id}`); };
  const generate = useMutation({ mutationFn: () => demo.generate(prompt), onSuccess: result => created(result.template.id) });
  const manual = useMutation({ mutationFn: () => demo.create({ title: "Untitled employee survey", description: null, setting: null, audience: "signed_in", audience_user_id: null, questions: [{ ...blankQuestion(), text: "How is your shift going?" }] }), onSuccess: result => created(result.id) });
  if (isPending) return <div className="product-page" role="status">Opening workspace…</div>;
  if (!session) return <div className="product-page"><h1>Your survey workspace</h1><Link href="/demo">Enter with a pass</Link> or <Link href="/signin">sign in</Link>.</div>;
  if (!me?.may_author) return <div className="product-page"><h1>Survey access</h1><p>This account can answer surveys. Creating surveys requires an author account.</p><Link href="/respond">Your surveys</Link></div>;
  const data = surveys.data ?? [];
  const started = data.reduce((sum, row) => sum + row.started, 0);
  const completed = data.reduce((sum, row) => sum + row.completed, 0);
  const cap = access.data;
  const canCreate = !!cap?.active && (cap.survey_limit === null || cap.surveys_created < cap.survey_limit);
  const pending = generate.isPending || manual.isPending;
  return <div className="product-page">
    <header className="page-heading"><div><p className="eyebrow">LISTEN. UNDERSTAND. ACT.</p><h1>{cap?.company ?? "Your workspace"}</h1><p>Turn employee feedback into a useful conversation.</p></div><Link className="btn" href="/#walkthrough">See the walkthrough</Link></header>
    {cap && <div className="access-strip"><strong>{cap.mode === "demo" ? `${cap.surveys_created} of 3 demo surveys created` : cap.mode === "customer" ? `Included with ${cap.product}` : "Company workspace"}</strong><span>{cap.expires_at ? `Access until ${new Date(cap.expires_at).toLocaleDateString()}` : "No access expiry"}</span>{cap.monthly_response_allowance !== null && <span>{cap.sessions_started_this_month} / {cap.monthly_response_allowance} response sessions this UTC month</span>}<span>{cap.active ? "Active" : "Results remain available. Creation and AI work are paused."}</span></div>}
    <div className="metric-grid"><article><span>Surveys</span><strong>{data.length}</strong><small>Currently stored</small></article><article><span>Started</span><strong>{started}</strong><small>Stored respondent sessions</small></article><article><span>Completed</span><strong>{completed}</strong><small>Reached the end</small></article><article><span>Completion</span><strong>{started ? `${Math.round(completed / started * 100)}%` : "No data"}</strong><small>Completed / started</small></article></div>
    <section className="product-card create-survey"><div><p className="eyebrow">START WITH WHAT YOU NEED TO KNOW</p><h2>Describe your next survey</h2><p>The AI saves a draft for you to review. Publishing freezes its questions.</p></div><form onSubmit={event => { event.preventDefault(); generate.mutate(); }}><label htmlFor="survey-brief">What do you want to learn?</label><textarea id="survey-brief" value={prompt} onChange={event => setPrompt(event.target.value)} required maxLength={4000} rows={4} /><div className="action-row"><button className="btn btn-primary" disabled={!canCreate || pending}>{generate.isPending ? "Drafting…" : "Generate a survey"}</button><button type="button" className="btn" disabled={!canCreate || pending} onClick={() => manual.mutate()}>{manual.isPending ? "Creating…" : "Build manually"}</button></div></form><p className="muted">Each successfully saved new draft uses one survey. Edits and failed generation do not. Deleting a survey does not restore its allowance. AI work is subject to the shared demo budget.</p>{(generate.error || manual.error) && <p role="alert" className="error-text">{(generate.error || manual.error)?.message}</p>}{!canCreate && cap && <p><a href="mailto:pawankapkoti3889@gmail.com?subject=Activate%20Elenchus">Activate with a qualifying KapkotiSolution purchase</a> to create more surveys.</p>}</section>
    <section><div className="page-heading"><h2>Your surveys</h2><label>Status <select value={filter} onChange={event => setFilter(event.target.value)}><option value="all">All</option><option value="draft">Draft</option><option value="published">Open</option><option value="closed">Closed</option></select></label></div>
    {surveys.isPending && <p role="status">Loading surveys…</p>}{(surveys.error || access.error) && <p role="alert">{(surveys.error || access.error)?.message}</p>}
    <div className="survey-grid">{data.filter(row => filter === "all" || row.status === filter).map(row => <article className="product-card" key={row.id}><span className="status-tag">{row.status === "published" ? "Open" : row.status}</span><h3><Link href={`/surveys/${row.id}`}>{row.title}</Link></h3><p>{row.completed} completed · {row.in_progress} in progress · {row.abandoned} finished early</p><div className="action-row"><Link href={`/surveys/${row.id}`} className="btn">{row.status === "draft" ? "Review draft" : "Manage & share"}</Link><Link href={`/surveys/${row.id}/results`}>Results →</Link></div></article>)}</div>
    {!surveys.isPending && data.length === 0 && <p>Your first survey will appear here after you create it.</p>}</section>
  </div>;
}
