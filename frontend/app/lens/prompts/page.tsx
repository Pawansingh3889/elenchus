"use client";

import { useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Gate } from "@/components/lens/Chart";
import { dollars, milliseconds, moment } from "@/lib/lensFormat";
import { useActivatePrompt, useMe, usePromptBody, usePromptFamily, useSavePrompt } from "@/lib/queries";

/**
 * The conduct prompt, versioned. Saving never edits a version: it adds the next one, and
 * nothing changes for respondents until a version is activated. Every version shows what
 * the turns run on it cost, which is what a prompt change should be judged by.
 */
export default function PromptsPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const family = usePromptFamily(admin);
  const [selected, setSelected] = useState<string | null>(null);
  const shown = selected ?? family.data?.active ?? null;
  const body = usePromptBody(shown, admin);
  const save = useSavePrompt();
  const activate = useActivatePrompt();
  const [confirming, setConfirming] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const newest = family.data?.versions.at(-1)?.name ?? null;

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Conduct prompt</h1>
        </div>
        <p className="lens-provenance">
          {family.data
            ? `Live: ${family.data.active}. The code's default is ${family.data.default}; activating any version replaces it from the next turn, and activating an older one rolls back.`
            : "Loading versions…"}
        </p>
        <ErrorBanner error={family.error ?? body.error ?? save.error ?? activate.error} />
        {saved ? <p className="lens-ok">Saved as {saved}. It is not live until you activate it.</p> : null}

        <div className="lens-table-wrap">
          <table className="lens-table">
            <thead>
              <tr>
                <th>Version</th>
                <th>Source</th>
                <th>Saved</th>
                <th>Note</th>
                <th className="num">Turns</th>
                <th className="num">Runs</th>
                <th className="num">Median turn</th>
                <th className="num">Cost</th>
                <th>Live</th>
              </tr>
            </thead>
            <tbody>
              {family.data?.versions.map((version) => (
                <tr key={version.name}>
                  <td>
                    <button type="button" className="link-btn" onClick={() => setSelected(version.name)}>
                      {version.name}
                    </button>
                    {version.name === shown ? " (open)" : ""}
                  </td>
                  <td>{version.source === "file" ? "file" : "saved here"}</td>
                  <td>
                    {version.created_at
                      ? `${moment(version.created_at)}${version.created_by_name ? ` by ${version.created_by_name}` : ""}`
                      : ""}
                  </td>
                  <td>{version.note ?? ""}</td>
                  <td className="num">{version.turns ?? "not traced"}</td>
                  <td className="num">{version.runs ?? ""}</td>
                  <td className="num">{version.turn_ms_p50 === null ? "" : milliseconds(version.turn_ms_p50)}</td>
                  <td className="num">{version.turns === null ? "" : dollars(version.cost_usd)}</td>
                  <td>
                    {version.active ? (
                      <span className="lens-badge">live</span>
                    ) : confirming === version.name ? (
                      <span className="actions">
                        <button
                          type="button"
                          className="btn btn-primary"
                          disabled={activate.isPending}
                          onClick={() => activate.mutate(version.name, { onSettled: () => setConfirming(null) })}
                        >
                          Make {version.name} live
                        </button>
                        <button type="button" className="btn btn-quiet" onClick={() => setConfirming(null)}>
                          Cancel
                        </button>
                      </span>
                    ) : (
                      <button type="button" className="btn btn-secondary" onClick={() => setConfirming(version.name)}>
                        Activate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {shown && body.data ? (
          // Keyed by version, so opening another version mounts a fresh editor holding its
          // text, instead of copying the text into state from an effect.
          <PromptEditor
            key={body.data.name}
            from={body.data.name}
            initial={body.data.body}
            nextName={nextName(newest)}
            saving={save.isPending}
            onSave={(draft, note) =>
              save.mutate(
                { body: draft, note },
                {
                  onSuccess: (next) => {
                    const created = next.versions.at(-1)?.name ?? null;
                    setSaved(created);
                    setSelected(created);
                  },
                },
              )
            }
          />
        ) : null}
      </div>
    </Gate>
  );
}

function PromptEditor({
  from,
  initial,
  nextName,
  saving,
  onSave,
}: {
  from: string;
  initial: string;
  nextName: string;
  saving: boolean;
  onSave: (draft: string, note: string | null) => void;
}) {
  const [draft, setDraft] = useState(initial);
  const [note, setNote] = useState("");
  return (
    <section className="card lens-prompt-editor">
      <div className="card-label">
        Editing from {from}. Saving creates {nextName}.
      </div>
      <label className="stack">
        <span className="muted">Prompt text</span>
        <textarea value={draft} onChange={(e) => setDraft(e.target.value)} spellCheck={false} />
      </label>
      <label className="stack">
        <span className="muted">What changed, and why (optional)</span>
        <input className="field" value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
      </label>
      <div className="actions">
        <button
          type="button"
          className="btn btn-primary"
          disabled={saving || draft.trim() === "" || draft === initial}
          onClick={() => onSave(draft, note.trim() || null)}
        >
          {saving ? "Saving…" : "Save as a new version"}
        </button>
        {draft !== initial ? (
          <button type="button" className="btn btn-quiet" onClick={() => setDraft(initial)}>
            Discard changes
          </button>
        ) : null}
      </div>
    </section>
  );
}

function nextName(newest: string | null): string {
  const match = newest?.match(/^(.*_v)(\d+)$/);
  return match ? `${match[1]}${Number(match[2]) + 1}` : "the next version";
}
