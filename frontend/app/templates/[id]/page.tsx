"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";

import { LivePreview } from "@/components/LivePreview";
import { clearedBy, followOptionRename, remapConditions, repairConditionsFor } from "@/lib/conditions";
import { QuestionEditor } from "@/components/QuestionEditor";
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
import { useDraftNoteStore, useUserStore } from "@/lib/store";
import type { QuestionInput } from "@/lib/types";

const blankQuestion = (): QuestionInput => ({
  text: "",
  answer_type: "short_text",
  options: [],
  allow_other: false,
  required: true,
  allow_follow_ups: false,
  show_when: null,
});

export default function BuilderPage({ params }: { params: Promise<{ id: string }> }) {
  const msg = useT();
  const { id } = use(params);
  const currentUserId = useUserStore((s) => s.currentUserId);
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
  const [questions, setQuestions] = useState<QuestionInput[]>([]);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  // How many visibility conditions the last reorder/delete had to clear.
  const [dropped, setDropped] = useState(0);
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
    setQuestions(
      template.questions.map((q) => ({
        text: q.text,
        answer_type: q.answer_type,
        options: q.options,
        allow_other: q.allow_other,
        required: q.required,
        allow_follow_ups: q.allow_follow_ups,
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

  // Editing a question can orphan a *later* question's condition: change the type and
  // the options go, remove an option and a condition naming it describes an answer that
  // can no longer be given. Repositioning is not the only edit conditions depend on.
  //
  // An option RENAME is followed before repair judges anything. This runs on every
  // keystroke, so "Days" being edited to "Nights" passes through "Day", "Da"… and a
  // repair-only pass cleared the condition at the first non-matching keystroke, then
  // had no way to restore it when the author finished typing.
  const patchQuestion = (i: number, patch: Partial<QuestionInput>) =>
    setQuestions((qs) => {
      const patched = qs.map((q, j) => (j === i ? { ...q, ...patch } : q));
      const touchesAnswers = "answer_type" in patch || "options" in patch || "allow_other" in patch;
      if (!touchesAnswers) return patched;
      const followed =
        "options" in patch && patch.options
          ? followOptionRename(patched, i, qs[i].options, patch.options)
          : patched;
      const next = repairConditionsFor(followed, i);
      setDropped(clearedBy(followed, next));
      return next;
    });
  const addQuestion = () => setQuestions((qs) => [...qs, blankQuestion()]);
  // Deleting or reordering shifts positions, and conditions are keyed by position —
  // so both have to repoint them or a condition silently starts referring to whatever
  // question moved into that slot.
  const removeQuestion = (i: number) =>
    setQuestions((qs) => {
      const order = qs.map((_, j) => j).filter((j) => j !== i);
      const next = remapConditions(order.map((j) => qs[j]), order);
      setDropped(clearedBy(qs, next));
      return next;
    });
  const moveQuestion = (i: number, dir: number) =>
    setQuestions((qs) => {
      const j = i + dir;
      if (j < 0 || j >= qs.length) return qs;
      const order = qs.map((_, k) => k);
      [order[i], order[j]] = [order[j], order[i]];
      const next = remapConditions(order.map((k) => qs[k]), order);
      setDropped(clearedBy(qs, next));
      return next;
    });

  // Which questions the server last objected to, so the complaint can sit on the card
  // it belongs to. A message under the description is a scroll away from a question far
  // down the list, and the author has to match "Question 4" to a card by counting.
  const rejected = [update.error, publish.error, refine.error]
    .flatMap((e) => (e instanceof ApiError ? e.questions : []))
    .filter((v, i, all) => all.indexOf(v) === i);

  // Known-bad before the server is even asked: a condition with nothing to match, and a
  // select with nothing to choose. Both are states the builder can reach, so Publish
  // should say why it is unavailable rather than failing after a round trip.
  const blockers = questions.flatMap((q, i) => {
    const problems: string[] = [];
    if (q.show_when && !q.show_when.value.trim()) problems.push(msg.builder.conditionHasNoAnswer);
    if ((q.answer_type === "single_select" || q.answer_type === "multi_select") && !q.options.length)
      problems.push(msg.builder.selectHasNoOptions);
    return problems.map((p) => msg.builder.publishBlocker(i + 1, p));
  });

  const body = { title, description: description || null, questions };
  const save = () => update.mutate(body);
  const onPublish = async () => {
    try {
      await update.mutateAsync(body);
      await publish.mutateAsync();
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
      setQuestions(
        revised.questions.map((q) => ({
          text: q.text,
          answer_type: q.answer_type,
          options: q.options,
          allow_other: q.allow_other,
          required: q.required,
          allow_follow_ups: q.allow_follow_ups,
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

  return (
    <div className="builder">
      <div className="builder-main">
        <div className="builder-head">
          <input
            className="builder-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={msg.builder.titlePlaceholder}
          />
          <div className="builder-actions">
            <span className={`pill pill-${template.status}`}>{template.status}</span>
            <Link href={`/templates/${template.id}/results`} className="btn btn-secondary">
              {msg.builder.responses}
            </Link>
            <button className="btn btn-secondary" onClick={save} disabled={update.isPending}>
              {update.isPending ? msg.common.saving : msg.common.save}
            </button>
            <button
              className="btn btn-primary"
              onClick={onPublish}
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
          {dropped > 0 ? (
          <div className="notice">
            {msg.builder.conditionsCleared(dropped)}
            <button className="link-btn" onClick={() => setDropped(0)}>
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
              onChange={(patch) => patchQuestion(i, patch)}
              earlier={questions.slice(0, i)}
              onRemove={() => removeQuestion(i)}
              onMove={(dir) => moveQuestion(i, dir)}
            />
          ))}
          <button className="add-question" onClick={addQuestion}>
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
