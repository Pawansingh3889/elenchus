"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { answerTypes, blankQuestion, demo, type Access, type Draft, type Question, type Template } from "@/lib/demo";
import { useSession } from "@/lib/queries";

function SurveyEditor({ initial, access }: { initial: Template; access: Access | undefined }) {
  const [draft, setDraft] = useState<Draft>(initial);
  const [freeze, setFreeze] = useState(false);
  const [deleteConfirmed, setDeleteConfirmed] = useState(false);
  const [link, setLink] = useState("");
  const [copied, setCopied] = useState(false);
  const qc = useQueryClient();
  const router = useRouter();
  const editable = initial.status === "draft" && access?.active;
  const refresh = () => { void qc.invalidateQueries({ queryKey: ["template", initial.id] }); void qc.invalidateQueries({ queryKey: ["dashboard"] }); };
  const save = useMutation({ mutationFn: () => demo.update(initial.id, { ...draft, questions: draft.questions.map(question => ({ ...question, options: question.options.map(text => text.trim()).filter(Boolean) })) }), onSuccess: refresh });
  const publish = useMutation({ mutationFn: () => demo.publish(initial.id), onSuccess: refresh });
  const close = useMutation({ mutationFn: () => demo.close(initial.id), onSuccess: refresh });
  const remove = useMutation({ mutationFn: () => demo.remove(initial.id), onSuccess: () => { void qc.invalidateQueries({ queryKey: ["dashboard"] }); router.push("/workspace"); } });
  const share = useMutation({ mutationFn: () => demo.share(initial.id), onSuccess: data => setLink(`${window.location.origin}/s#${data.token}`) });
  const duplicate = useMutation({ mutationFn: () => demo.create({ ...draft, title: `${draft.title} (copy)` }), onSuccess: data => { void qc.invalidateQueries({ queryKey: ["access"] }); router.push(`/surveys/${data.id}`); } });
  const dirty = JSON.stringify(draft) !== JSON.stringify(initial);
  const busy = save.isPending || publish.isPending || close.isPending || remove.isPending || duplicate.isPending;
  const updateQuestion = (index: number, change: Partial<Question>) => setDraft({ ...draft, questions: draft.questions.map((question, i) => i === index ? { ...question, ...change } : question) });
  const removeQuestion = (index: number) => setDraft({ ...draft, questions: draft.questions.filter((_, i) => i !== index).map(question => ({ ...question, show_when: !question.show_when || question.show_when.question === index ? null : { ...question.show_when, question: question.show_when.question > index ? question.show_when.question - 1 : question.show_when.question } })) });
  const error = save.error || publish.error || close.error || share.error || remove.error || duplicate.error;
  return <>
    <header className="page-heading"><div><Link href="/workspace">← Your workspace</Link><h1>{initial.title}</h1><p><span className="status-tag">{initial.status === "published" ? "Open for responses" : initial.status}</span> {initial.questions.length} questions</p></div><Link className="btn" href={`/surveys/${initial.id}/results`}>View results →</Link></header>
    {error && <p className="notice error-text" role="alert">{error.message}</p>}
    {initial.status === "published" && <section className="product-card"><h2>Invite people to answer</h2><p>The respondent link opens only this survey. Do not share your workspace pass with respondents.</p><button className="btn btn-primary" disabled={share.isPending || !access?.active} onClick={() => share.mutate()}>{share.isPending ? "Preparing…" : "Create respondent link"}</button>{link && <div className="share-box"><label htmlFor="respondent-link">Respondent link, valid for up to 14 days within your access period</label><input id="respondent-link" value={link} readOnly onFocus={event => event.currentTarget.select()} /><button className="btn" onClick={async () => { try { await navigator.clipboard.writeText(link); setCopied(true); } catch { setCopied(false); } }}>{copied ? "Copied" : "Copy link"}</button><p>To try it yourself, paste the link into a separate browser profile. Your author workspace will stay open here.</p></div>}</section>}
    <form onSubmit={event => { event.preventDefault(); save.mutate(); }}>
      <fieldset className="product-card" disabled={!editable || busy}><legend>Survey details</legend>
        <label htmlFor="survey-title">Title</label><input id="survey-title" required maxLength={300} value={draft.title} onChange={event => setDraft({ ...draft, title: event.target.value })} />
        <label htmlFor="survey-description">Introduction for participants</label><textarea id="survey-description" rows={2} value={draft.description ?? ""} onChange={event => setDraft({ ...draft, description: event.target.value || null })} />
        <label htmlFor="survey-setting">Context for the interviewer</label><textarea id="survey-setting" maxLength={2000} rows={2} value={draft.setting ?? ""} onChange={event => setDraft({ ...draft, setting: event.target.value || null })} />
        <p className="muted">For respondent links, the survey audience is anyone signed in to this workspace. Participants receive a session through their invitation.</p>
      </fieldset>
      <div className="question-list">{draft.questions.map((question, index) => <fieldset className="product-card question-editor" key={index} disabled={!editable || busy}><legend>Question {index + 1}</legend>
        <label htmlFor={`question-${index}`}>Question text</label><textarea id={`question-${index}`} required value={question.text} rows={2} onChange={event => updateQuestion(index, { text: event.target.value })} />
        <div className="form-columns"><label>Answer type<select value={question.answer_type} onChange={event => { const type = answerTypes.find(type => type === event.target.value); if (type) updateQuestion(index, { answer_type: type, options: type.includes("select") ? ["Yes", "No"] : [], unit: null, display_unit: null }); }}>{answerTypes.map(type => <option key={type} value={type}>{type.replaceAll("_", " ")}</option>)}</select></label><label>Follow-up questions<select value={question.follow_up_policy} onChange={event => { const policy = event.target.value; if (policy === "never" || policy === "when_unclear" || policy === "always_once") updateQuestion(index, { follow_up_policy: policy }); }}><option value="never">Never</option><option value="when_unclear">When unclear</option><option value="always_once">Always</option></select></label></div>
        {question.answer_type.includes("select") && <><label htmlFor={`options-${index}`}>Options, one per line</label><textarea id={`options-${index}`} value={question.options.join("\n")} rows={3} onChange={event => updateQuestion(index, { options: event.target.value.split("\n") })} /><label className="check-label"><input type="checkbox" checked={question.allow_other} onChange={event => updateQuestion(index, { allow_other: event.target.checked })} />Allow a written alternative</label></>}
        {question.answer_type === "rating" && <p className="muted">Rating scale: 1 to 5.</p>}
        <label className="check-label"><input type="checkbox" checked={question.required} onChange={event => updateQuestion(index, { required: event.target.checked })} />Required question</label>
        {question.show_when && <p className="notice">Shown when question {question.show_when.question + 1} {question.show_when.op.replaceAll("_", " ")} “{question.show_when.value}”. <button type="button" className="btn" onClick={() => updateQuestion(index, { show_when: null })}>Remove condition</button></p>}
        {editable && <button type="button" className="text-button" onClick={() => removeQuestion(index)}>Remove question</button>}
      </fieldset>)}</div>
      {editable && <div className="action-row"><button type="button" className="btn" disabled={busy || (access?.question_limit !== null && access?.question_limit !== undefined && draft.questions.length >= access.question_limit)} onClick={() => setDraft({ ...draft, questions: [...draft.questions, blankQuestion()] })}>Add question</button><button className="btn btn-primary" disabled={busy || !dirty}>{save.isPending ? "Saving…" : "Save changes"}</button>{dirty && <span>Unsaved changes</span>}</div>}
    </form>
    <section className="product-card">
      {initial.status === "draft" ? <><h2>Ready to ask?</h2><p>Publishing freezes the questions. Later changes require a new survey. Save and review your questions first.</p><label className="check-label"><input type="checkbox" checked={freeze} onChange={event => setFreeze(event.target.checked)} />I have reviewed the saved questions and want to publish them.</label><button className="btn btn-primary" disabled={!freeze || dirty || busy || !access?.active || !draft.questions.length} onClick={() => publish.mutate()}>{publish.isPending ? "Publishing…" : "Publish and freeze questions"}</button></> : <><h2>Manage this survey</h2><p>Published questions are frozen to preserve what people were asked.</p>{initial.status === "published" && <button className="btn" disabled={busy} onClick={() => close.mutate()}>Close to new responses</button>}</>}
      <div className="action-row"><button className="btn" disabled={busy || dirty || !access?.active || (access?.survey_limit !== null && access?.survey_limit !== undefined && access.surveys_created >= access.survey_limit)} onClick={() => duplicate.mutate()}>Duplicate as a new draft</button><small>Uses another survey allowance.</small></div>
      <details><summary>Delete an unanswered survey</summary><p>Deletion is permanent and allowed only before any respondent session exists. It does not restore your survey allowance.</p><label className="check-label"><input type="checkbox" checked={deleteConfirmed} onChange={event => setDeleteConfirmed(event.target.checked)} />Permanently delete this survey.</label><button className="btn" disabled={!deleteConfirmed || busy} onClick={() => remove.mutate()}>Delete survey</button></details>
    </section>
  </>;
}

export default function SurveyPage() {
  const { id } = useParams<{ id: string }>();
  const { data: session } = useSession();
  const query = useQuery({ queryKey: ["template", id, session?.id], queryFn: () => demo.template(id), enabled: !!session });
  const access = useQuery({ queryKey: ["access", session?.id], queryFn: demo.access, enabled: !!session });
  return <div className="product-page">{!session && <p><Link href="/demo">Enter your workspace</Link> to review this survey.</p>}{query.isFetching && <p role="status">Loading survey…</p>}{(query.error || access.error) && <p role="alert">{(query.error || access.error)?.message}</p>}{query.data && <SurveyEditor key={JSON.stringify(query.data)} initial={query.data} access={access.data} />}</div>;
}
