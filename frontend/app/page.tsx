"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useCreateTemplate, useCurrentUser, useGenerateTemplate, useTemplates } from "@/lib/queries";
import { useUserStore } from "@/lib/store";

export default function Home() {
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: templates, isLoading, error } = useTemplates();
  const create = useCreateTemplate();
  const generate = useGenerateTemplate();
  const router = useRouter();
  const [prompt, setPrompt] = useState("");

  // Build is author-only on the backend; a respondent landing here (e.g. after
  // switching users in the top bar) belongs on Respond, not on a page of 403s.
  const isRespondent = currentUser?.role === "respondent";
  useEffect(() => {
    if (isRespondent) router.replace("/respond");
  }, [isRespondent, router]);

  if (!currentUserId) {
    return <div className="empty">Pick a user in the top bar to start authoring.</div>;
  }
  if (isRespondent) {
    return <div className="empty">Taking you to Respond…</div>;
  }

  async function onCreate() {
    const t = await create.mutateAsync({ title: "Untitled survey", questions: [] });
    router.push(`/templates/${t.id}`);
  }

  async function onGenerate() {
    if (!prompt.trim()) return;
    const t = await generate.mutateAsync(prompt.trim());
    router.push(`/templates/${t.id}`);
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>Survey templates</h1>
        <button className="btn btn-primary" onClick={onCreate} disabled={create.isPending}>
          {create.isPending ? "Creating…" : "New template"}
        </button>
      </div>

      {create.error ? (
        <div className="error-text">{(create.error as Error).message}</div>
      ) : null}

      <div className="card generate-card">
        <div className="card-label">✦ Draft with AI</div>
        <textarea
          placeholder="Describe the survey… e.g. An onboarding survey for factory staff: their role, the systems they use daily, and their biggest data frustrations."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <div className="generate-actions">
          <button
            className="btn btn-ai"
            onClick={onGenerate}
            disabled={generate.isPending || !prompt.trim()}
          >
            {generate.isPending ? "Drafting…" : "✦ Generate draft"}
          </button>
        </div>
        {generate.error ? (
          <div className="error-text">{(generate.error as Error).message}</div>
        ) : null}
      </div>

      {isLoading ? <div className="muted">Loading…</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}

      <div className="template-list">
        {templates?.map((t) => (
          <Link key={t.id} href={`/templates/${t.id}`} className="template-row">
            <div>
              <div className="template-title">{t.title}</div>
              <div className="template-meta">
                {t.question_count} question{t.question_count === 1 ? "" : "s"}
                {" · edited "}
                {new Date(t.updated_at).toLocaleString(undefined, {
                  day: "numeric",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
            <span className={`pill pill-${t.status}`}>{t.status}</span>
          </Link>
        ))}
        {templates && templates.length === 0 ? (
          <div className="muted">No templates yet. Create one or draft with AI.</div>
        ) : null}
      </div>
    </div>
  );
}
