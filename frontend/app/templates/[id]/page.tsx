"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";

import { LivePreview } from "@/components/LivePreview";
import { QuestionEditor } from "@/components/QuestionEditor";
import {
  useCurrentUser,
  useDeleteTemplate,
  usePublishTemplate,
  useTemplate,
  useUpdateTemplate,
} from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import type { QuestionInput } from "@/lib/types";

const blankQuestion = (): QuestionInput => ({
  text: "",
  answer_type: "short_text",
  options: [],
  allow_other: false,
  required: true,
  allow_follow_ups: false,
});

export default function BuilderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: template, isLoading, error } = useTemplate(id);
  const update = useUpdateTemplate(id);
  const publish = usePublishTemplate(id);
  const remove = useDeleteTemplate(id);
  const router = useRouter();

  const [loadedId, setLoadedId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [questions, setQuestions] = useState<QuestionInput[]>([]);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

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
      })),
    );
  }

  if (!currentUserId) return <div className="empty">Pick a user in the top bar.</div>;
  if (isRespondent) return <div className="empty">Taking you to Respond…</div>;
  if (isLoading) return <div className="muted">Loading…</div>;
  if (error || !template) {
    return <div className="error-text">{error ? (error as Error).message : "Not found"}</div>;
  }

  const patchQuestion = (i: number, patch: Partial<QuestionInput>) =>
    setQuestions((qs) => qs.map((q, j) => (j === i ? { ...q, ...patch } : q)));
  const addQuestion = () => setQuestions((qs) => [...qs, blankQuestion()]);
  const removeQuestion = (i: number) => setQuestions((qs) => qs.filter((_, j) => j !== i));
  const moveQuestion = (i: number, dir: number) =>
    setQuestions((qs) => {
      const j = i + dir;
      if (j < 0 || j >= qs.length) return qs;
      const copy = [...qs];
      [copy[i], copy[j]] = [copy[j], copy[i]];
      return copy;
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

  return (
    <div className="builder">
      <div className="builder-main">
        <div className="builder-head">
          <input
            className="builder-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Survey title"
          />
          <div className="builder-actions">
            <span className={`pill pill-${template.status}`}>{template.status}</span>
            <Link href={`/templates/${template.id}/results`} className="btn btn-secondary">
              Responses
            </Link>
            <button className="btn btn-secondary" onClick={save} disabled={update.isPending}>
              {update.isPending ? "Saving…" : "Save"}
            </button>
            <button
              className="btn btn-primary"
              onClick={onPublish}
              disabled={publish.isPending || questions.length === 0}
            >
              {publish.isPending ? "Publishing…" : "Publish"}
            </button>
            {confirmingDelete ? (
              <>
                <button className="btn btn-danger" onClick={onDelete} disabled={remove.isPending}>
                  {remove.isPending ? "Deleting…" : "Confirm delete"}
                </button>
                <button className="btn btn-secondary" onClick={() => setConfirmingDelete(false)}>
                  Cancel
                </button>
              </>
            ) : (
              <button className="btn btn-quiet" onClick={() => setConfirmingDelete(true)}>
                Delete
              </button>
            )}
          </div>
        </div>

        <textarea
          className="field builder-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
        />

        {update.error ? <div className="error-text">{(update.error as Error).message}</div> : null}
        {publish.error ? (
          <div className="error-text">{(publish.error as Error).message}</div>
        ) : null}
        {remove.error ? <div className="error-text">{(remove.error as Error).message}</div> : null}

        <div className="questions">
          {questions.map((q, i) => (
            <QuestionEditor
              key={i}
              index={i}
              total={questions.length}
              question={q}
              onChange={(patch) => patchQuestion(i, patch)}
              onRemove={() => removeQuestion(i)}
              onMove={(dir) => moveQuestion(i, dir)}
            />
          ))}
          <button className="add-question" onClick={addQuestion}>
            + Add question
          </button>
        </div>
      </div>

      <LivePreview questions={questions} />
    </div>
  );
}
