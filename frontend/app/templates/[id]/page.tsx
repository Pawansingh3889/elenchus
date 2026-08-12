"use client";

import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";

import { LivePreview } from "@/components/LivePreview";
import { QuestionEditor } from "@/components/QuestionEditor";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { SurveyNav } from "@/components/SurveyNav";
import { publishBlockers } from "@/lib/publishBlockers";
import { publishQuip } from "@/lib/publishQuip";
import { useDraftQuestions } from "@/lib/useDraftQuestions";
import {
  useCurrentUser,
  useDeleteTemplate,
  usePublishTemplate,
  useRefineTemplate,
  useTemplate,
  useUpdateTemplate,
} from "@/lib/queries";
import { ApiError } from "@/lib/api";
import { useT } from "@/lib/i18n/useT";
import { useDraftNoteStore, useLocaleStore, useUserStore } from "@/lib/store";
import type { SurveyAudience } from "@/lib/types";

export default function BuilderPage({ params }: { params: Promise<{ id: string }> }) {
  const msg = useT();
  const { id } = use(params);
  const currentUserId = useUserStore((s) => s.currentUserId);
  // Read here rather than through useT: the quip is chosen by locale, not
  // translated for it, so what it needs is which locale, not the strings.
  const locale = useLocaleStore((s) => s.locale);
  const currentUser = useCurrentUser();
  const { data: template, isLoading, error } = useTemplate(id);
  const update = useUpdateTemplate(id);
  const publish = usePublishTemplate(id);
  const remove = useDeleteTemplate(id);
  const refine = useRefineTemplate(id);
  const router = useRouter();

  const [loadedId, setLoadedId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const draft = useDraftQuestions();
  const questions = draft.questions;
  const [audience, setAudience] = useState<SurveyAudience>("respondents");
  const [setting, setSetting] = useState("");
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [confirmingPublish, setConfirmingPublish] = useState(false);
  const [instruction, setInstruction] = useState("");
  // Seed the Refine panel with the note from the generate that opened this draft…
  const [notes, setNotes] = useState<string[]>(() => {
    const pending = useDraftNoteStore.getState().pending[id];
    return pending ? [pending] : [];
  });
  // …then clear it so revisiting the builder doesn't re-show it.
  useEffect(() => {
    useDraftNoteStore.getState().clearPendingNote(id);
  }, [id]);

  const isRespondent = currentUser?.role === "respondent";
  useEffect(() => {
    if (isRespondent) router.replace("/respond");
  }, [isRespondent, router]);

  // Initialise the editable form from the fetched template once, and again if the
  // route id OR the acting user changes — adjusting state during render, not in an
  // effect. Keying on the user too stops one author's unsaved edits from surviving a
  // switch and being saved under the next author's identity.
  const formKey = template ? `${template.id}:${currentUserId}` : null;
  if (template && formKey !== loadedId) {
    setLoadedId(formKey);
    setTitle(template.title);
    setDescription(template.description ?? "");
    setAudience(template.audience);
    setSetting(template.setting ?? "");
    draft.reset(
      template.questions.map((q) => ({
        text: q.text,
        answer_type: q.answer_type,
        options: q.options,
        allow_other: q.allow_other,
        required: q.required,
        follow_up_policy: q.follow_up_policy,
        show_when: q.show_when ?? null,
      })),
    );
  }

  if (!currentUserId) return <div className="empty">{msg.builder.pickUser}</div>;
  if (isRespondent) return <div className="empty">{msg.home.goingToRespond}</div>;
  if (isLoading) return <div className="muted">{msg.common.loading}</div>;
  if (error || !template) {
    return <div className="error-text">{error ? (error as Error).message : msg.common.notFound}</div>;
  }

  // Which questions the server last objected to, so the complaint can sit on the card
  // it belongs to. A message under the description is a scroll away from a question far
  // down the list, and the author has to match "Question 4" to a card by counting.
  const rejected = [update.error, publish.error, refine.error]
    .flatMap((e) => (e instanceof ApiError ? e.questions : []))
    .filter((v, i, all) => all.indexOf(v) === i);

  const blockers = publishBlockers(questions, msg.builder);

  // audience and setting ride on every write although nothing here edits them: a save
  // replaces the whole template, so leaving one out clears it. Read from the template,
  // sent straight back.
  const body = {
    title,
    description: description || null,
    audience,
    // Empty box means no setting, not an empty one: null is what "not described" is
    // stored as, and the engine reads a blank string the same way.
    setting: setting.trim() || null,
    questions,
  };
  const save = () => update.mutate(body);
  const onPublish = async () => {
    // Closed before the request, not after it: publishing can fail, and the error is
    // rendered on the page below. Leaving the dialog up would put it behind a modal the
    // author has to dismiss before they can read why it did not work.
    setConfirmingPublish(false);
    try {
      await update.mutateAsync(body);
      await publish.mutateAsync();
      // Onward, not back to the questions they just froze. Publishing is the end of
      // building and the start of waiting for answers, and the report is where those
      // arrive: it reads "nobody has answered yet" until they do, which is the true
      // state and more use than the editor they published from.
      router.push(`/templates/${id}/results`);
    } catch {
      // Rendered from update.error / publish.error below.
    }
  };
  const onDelete = () => remove.mutate(undefined, { onSuccess: () => router.push("/") });
  const onRefine = async () => {
    const text = instruction.trim();
    if (!text) return;
    try {
      // Persist what the author currently sees, so the AI refines that, not a stale draft.
      await update.mutateAsync(body);
      const { template: revised, note } = await refine.mutateAsync(text);
      setTitle(revised.title);
      setDescription(revised.description ?? "");
      // The server's policy, not the local copy: refine is not offered the field and
      // cannot change it, so this only ever re-states what was already saved. Re-seeding
      // it with the rest keeps one source of truth for the whole form.
      setAudience(revised.audience);
      setSetting(revised.setting ?? "");
      draft.reset(
        revised.questions.map((q) => ({
          text: q.text,
          answer_type: q.answer_type,
          options: q.options,
          allow_other: q.allow_other,
          required: q.required,
          follow_up_policy: q.follow_up_policy,
          // The refined draft is the server's, conditions and all — dropping this would
          // silently strip every condition each time the author refined.
          show_when: q.show_when ?? null,
        })),
      );
      setNotes((n) => [...n, note || "Updated the draft."]);
      setInstruction("");
    } catch {
      // Surfaced via update.error / refine.error below.
    }
  };

  const probing = questions.filter((q) => q.follow_up_policy === "always_once").length;
  const republishing = template?.status !== "draft";
  const quip = publishQuip(questions, republishing, locale);

  return (
    <div className="builder">
      {confirmingPublish ? (
        <ConfirmDialog
          title={msg.builder.publishTitle(title.trim() || msg.builder.titlePlaceholder)}
          confirmLabel={msg.common.publish}
          cancelLabel={msg.common.cancel}
          pending={publish.isPending || update.isPending}
          onConfirm={onPublish}
          onCancel={() => setConfirmingPublish(false)}
        >
          <p>{msg.builder.publishShape(questions.length, probing)}</p>
          <p>{republishing ? msg.builder.publishAgain : msg.builder.publishFreezes}</p>
          {/* English only, and absent rather than translated: everything load-bearing
              above is said in every locale, and this line is not. */}
          {quip ? <p className="modal-aside">{quip}</p> : null}
        </ConfirmDialog>
      ) : null}
      <div className="builder-main">
        <SurveyNav templateId={id} current="build" />
        <div className="builder-head">
          <input
            className="builder-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={msg.builder.titlePlaceholder}
          />
          <div className="builder-actions">
            <span className={`pill pill-${template.status}`}>{template.status}</span>
            <button className="btn btn-secondary" onClick={save} disabled={update.isPending}>
              {update.isPending ? msg.common.saving : msg.common.save}
            </button>
            <button
              className="btn btn-primary"
              onClick={() => setConfirmingPublish(true)}
              disabled={publish.isPending || questions.length === 0 || blockers.length > 0}
              title={blockers.length > 0 ? blockers.join("\n") : undefined}
            >
              {publish.isPending ? msg.common.publishing : msg.common.publish}
            </button>
            {confirmingDelete ? (
              <>
                <button className="btn btn-danger" onClick={onDelete} disabled={remove.isPending}>
                  {remove.isPending ? msg.common.deleting : msg.common.confirmDelete}
                </button>
                <button className="btn btn-secondary" onClick={() => setConfirmingDelete(false)}>
                  {msg.common.cancel}
                </button>
              </>
            ) : (
              <button className="btn btn-quiet" onClick={() => setConfirmingDelete(true)}>
                {msg.common.delete}
              </button>
            )}
          </div>
        </div>

        <textarea
          className="field builder-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={msg.builder.descriptionPlaceholder}
        />

        {update.error ? <div className="error-text">{(update.error as Error).message}</div> : null}
        {publish.error ? (
          <div className="error-text">{(publish.error as Error).message}</div>
        ) : null}
        {remove.error ? <div className="error-text">{(remove.error as Error).message}</div> : null}

        <div className="questions">
          {draft.dropped > 0 ? (
          <div className="notice">
            {msg.builder.conditionsCleared(draft.dropped)}
            <button className="link-btn" onClick={draft.dismissDropped}>
              {msg.common.dismiss}
            </button>
          </div>
        ) : null}
        {questions.map((q, i) => (
            <QuestionEditor
              key={i}
              index={i}
              total={questions.length}
              question={q}
              rejected={rejected.includes(i)}
              onChange={(patch) => draft.patch(i, patch)}
              earlier={questions.slice(0, i)}
              onRemove={() => draft.remove(i)}
              onMove={(dir) => draft.move(i, dir)}
            />
          ))}
          <button className="add-question" onClick={draft.add}>
            {msg.builder.addQuestion}
          </button>
        </div>
      </div>

      <div className="builder-side">
        <div className="card refine-card">
          <div className="card-label">{msg.builder.refineTitle}</div>
          <div className="refine-notes">
            {notes.length === 0 ? (
              <p className="muted refine-hint">
                Ask for a change — e.g. “make it shorter”, “add a question about pay”, or
                “change Q2 to multiple choice”. Your edits are saved first, then revised.
              </p>
            ) : (
              notes.map((note, i) => (
                <div key={i} className="refine-note">
                  ✦ {note}
                </div>
              ))
            )}
          </div>
          <form
            className="refine-form"
            onSubmit={(e) => {
              e.preventDefault();
              onRefine();
            }}
          >
            <input
              className="field"
              value={instruction}
              placeholder={msg.builder.refinePlaceholder}
              disabled={refine.isPending || update.isPending}
              onChange={(e) => setInstruction(e.target.value)}
            />
            <button
              className="btn btn-ai"
              type="submit"
              disabled={refine.isPending || update.isPending || !instruction.trim()}
            >
              {refine.isPending ? "Refining…" : "Refine"}
            </button>
          </form>
          {refine.error ? (
            <div className="error-text">{(refine.error as Error).message}</div>
          ) : null}
        </div>
        <LivePreview questions={questions} />
      </div>
    </div>
  );
}
