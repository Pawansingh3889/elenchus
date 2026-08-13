"use client";

import { useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { bandLabel, functionLabel, hatLabel, jobLabel } from "@/lib/audience";
import type { Messages } from "@/lib/i18n";
import { useT } from "@/lib/i18n/useT";
import {
  useAccountHistory,
  useCreateAccount,
  usePreviewAccount,
  useReplaceAccount,
} from "@/lib/queries";
import { useLocaleStore } from "@/lib/store";
import type {
  AccountChangeEntry,
  AccountImpact,
  AccountWrite,
  Band,
  Hat,
  JobFunction,
  Person,
} from "@/lib/types";

const FUNCTIONS: JobFunction[] = [
  "production",
  "quality",
  "health_safety",
  "technical",
  "planning",
  "hr",
  "finance",
  "supply_chain",
  "it",
  "executive",
];
const BANDS: Band[] = ["operative", "line_leader", "supervisor", "manager", "head", "director"];
const HATS: Hat[] = ["health_safety"];

/** Shared by every field, and lifted from SelectTrigger so a text box and a dropdown are
 *  the same object on the page. Only classes that already compile: an invented utility is
 *  a correct string that renders unstyled, which is what check-tailwind-classes.mjs is
 *  for. */
const FIELD =
  "min-h-[var(--tap)] w-full rounded-lg border border-line bg-raised px-3 text-sm text-ink " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";

interface Props {
  /** The account being changed, or null to create one. */
  person: Person | null;
  onClose: () => void;
}

/**
 * The one screen that decides what somebody is.
 *
 * One form for both jobs, because the update is a full replacement rather than a patch:
 * the server takes every field each time, so an edit is a create with the boxes already
 * filled. Only the email differs, and only because it cannot be changed afterwards.
 *
 * The form states the job (function and band, both required) and any hats; what the
 * account may do derives from that on the server. The rules about which combinations
 * are refused are deliberately NOT duplicated here: a second copy of them in a browser
 * is a copy that drifts from the one the database is actually protected by. So the
 * form submits, and the server's sentence is what the administrator reads.
 */
export function PersonDialog({ person, onClose }: Props) {
  const { admin: t, common, jobFunction: fn, band: bandT, hat: hatT } = useT();
  const locale = useLocaleStore((s) => s.locale);
  const create = useCreateAccount();
  const replace = useReplaceAccount();
  const preview = usePreviewAccount();
  const { data: history } = useAccountHistory(person?.id ?? null);

  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState(person?.display_name ?? "");
  const [jobFunction, setJobFunction] = useState<JobFunction>(person?.function ?? "production");
  const [band, setBand] = useState<Band>(person?.band ?? "operative");
  const [hats, setHats] = useState<Hat[]>(person?.hats ?? []);
  // The id itself is never sent to the browser, only whether one is set, so an edit
  // starts blank and a blank submit clears it. Said plainly under the field rather than
  // left for somebody to discover by saving.
  const [microsoftId, setMicrosoftId] = useState("");
  // The guardrail step. Saving an edit asks the server what would change first; when
  // open surveys are affected or authorship flips, the answer is shown and Save
  // becomes a decision rather than a reflex. The form is hidden meanwhile, which is
  // what lets `buildBody()` be called again on confirm and mean the same edit.
  const [impact, setImpact] = useState<AccountImpact | null>(null);

  const pending = create.isPending || replace.isPending || preview.isPending;
  const error = create.error ?? replace.error ?? preview.error;

  function toggleHat(hat: Hat) {
    setHats((current) =>
      current.includes(hat) ? current.filter((h) => h !== hat) : [...current, hat],
    );
  }

  function buildBody(): AccountWrite {
    return {
      display_name: displayName,
      function: jobFunction,
      band,
      // An empty box is an absent id, not an empty one. The server folds this too; doing
      // it here as well keeps the request honest about what it is asking for.
      microsoft_id: microsoftId.trim() || null,
      hats,
    };
  }

  function save() {
    const body = buildBody();
    const done = { onSuccess: onClose };
    if (person) replace.mutate({ id: person.id, data: body }, done);
    else create.mutate({ ...body, email }, done);
  }

  function submit() {
    // Creates save directly: the preview compares against an account as it stands, and
    // a new person stands nowhere yet. Edits ask first, and only interrupt when the
    // answer would surprise: reach moving on an open survey, or authorship flipping,
    // which the server derives because band order is its fact.
    if (!person) {
      save();
      return;
    }
    preview.mutate(
      { id: person.id, data: buildBody() },
      {
        onSuccess: (result) => {
          if (result.surveys.length > 0 || result.may_author_before !== result.may_author_after) {
            setImpact(result);
          } else {
            save();
          }
        },
      },
    );
  }

  return (
    <Dialog open onOpenChange={(open) => (open ? null : onClose())}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{person ? t.editTitle : t.newTitle}</DialogTitle>
          <DialogDescription>{person ? t.editSubtitle : t.newSubtitle}</DialogDescription>
        </DialogHeader>

        {error ? <ErrorBanner error={error} /> : null}

        {impact ? (
          <ImpactPanel
            impact={impact}
            pending={pending}
            onBack={() => setImpact(null)}
            onConfirm={save}
          />
        ) : null}

        <div className={impact ? "hidden" : "flex flex-col gap-4"}>
          {person ? null : (
            <label className="flex flex-col gap-1">
              <span className="text-sm font-medium text-ink">{t.emailLabel}</span>
              <input
                className={FIELD}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
              />
              <span className="text-xs text-muted">{t.emailFixed}</span>
            </label>
          )}

          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-ink">{t.nameLabel}</span>
            <input
              className={FIELD}
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-ink">{t.functionLabel}</span>
            <select
              className={FIELD}
              value={jobFunction}
              onChange={(e) => setJobFunction(e.target.value as JobFunction)}
            >
              {FUNCTIONS.map((f) => (
                <option key={f} value={f}>
                  {functionLabel(fn, f)}
                </option>
              ))}
            </select>
            <span className="text-xs text-muted">{t.functionHint}</span>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-ink">{t.bandLabel}</span>
            <select
              className={FIELD}
              value={band}
              onChange={(e) => setBand(e.target.value as Band)}
            >
              {BANDS.map((b) => (
                <option key={b} value={b}>
                  {bandLabel(bandT, b)}
                </option>
              ))}
            </select>
            <span className="text-xs text-muted">{t.bandHint}</span>
          </label>

          <fieldset className="flex flex-col gap-1">
            <legend className="text-sm font-medium text-ink">{t.hatsLabel}</legend>
            <span className="text-xs text-muted">{t.hatsHint}</span>
            <div className="flex flex-wrap gap-3 pt-1">
              {HATS.map((hat) => (
                <label key={hat} className="flex items-center gap-2 text-sm text-ink">
                  <input
                    type="checkbox"
                    checked={hats.includes(hat)}
                    onChange={() => toggleHat(hat)}
                  />
                  {hatLabel(hatT, hat)}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-ink">{t.entraLabel}</span>
            <input
              className={FIELD}
              value={microsoftId}
              onChange={(e) => setMicrosoftId(e.target.value)}
            />
            <span className="text-xs text-muted">{t.entraHint}</span>
          </label>

          {person && history && history.length > 0 ? (
            <div className="flex flex-col gap-1 border-t border-line pt-3">
              <span className="text-sm font-medium text-ink">{t.historyTitle}</span>
              {/* Why every reach number is what it is. The log is append-only on the
                  server; this renders the newest few because the question a dialog
                  answers is "what happened to this account lately", not "export it". */}
              <ul className="flex flex-col gap-1">
                {history.slice(0, 5).map((entry) => (
                  <li key={entry.id} className="text-xs text-muted">
                    {new Date(entry.changed_at).toLocaleDateString(locale)}
                    {" · "}
                    {entry.changed_by_name ?? t.historySomeone}
                    {": "}
                    {changeSummary(entry, t, fn, bandT)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>

        {impact ? null : (
          <DialogFooter>
            <Button variant="quiet" onClick={onClose} disabled={pending}>
              {common.cancel}
            </Button>
            <Button variant="primary" onClick={submit} disabled={pending}>
              {pending ? common.saving : common.save}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}

/** A snapshot's list-valued key, tolerant of rows from before the job model: new rows
 *  say `hats`, old rows say `groups`, and the log serves both as written. */
function names(snapshot: Record<string, unknown>, key: string): string[] {
  const value = snapshot[key];
  return Array.isArray(value) ? value.map((v) => String(v).replaceAll("_", " ")) : [];
}

/** One audit row as a sentence fragment: what changed, in the reader's language where
 *  the vocabulary still exists, and as the stored words for rows that predate it. */
function changeSummary(
  entry: AccountChangeEntry,
  t: Messages["admin"],
  fn: Messages["jobFunction"],
  bandT: Messages["band"],
): string {
  if (entry.kind === "created" || entry.before === null) return t.historyCreated;
  const { before, after } = entry;
  const parts: string[] = [];
  for (const key of ["hats", "groups"]) {
    const was = names(before, key);
    const now = names(after, key);
    const added = now.filter((v) => !was.includes(v));
    const removed = was.filter((v) => !now.includes(v));
    if (added.length) parts.push(t.historyAdded(added.join(", ")));
    if (removed.length) parts.push(t.historyRemoved(removed.join(", ")));
  }
  if (before.function !== after.function || before.band !== after.band) {
    const f = after.function as JobFunction | null;
    const b = after.band as Band | null;
    parts.push(
      t.historyJob(
        f && b ? `${functionLabel(fn, f)} · ${bandLabel(bandT, b)}` : String(after.function),
      ),
    );
  }
  // Legacy rows: a role change was the account type moving, still worth a word.
  if (before.role !== after.role && after.role !== undefined) {
    parts.push(t.historyJob(String(after.role)));
  }
  if (
    parts.length === 0 ||
    before.display_name !== after.display_name ||
    before.microsoft_id !== after.microsoft_id
  ) {
    parts.push(t.historyOther);
  }
  return parts.join(", ");
}

/** The pause between asking and doing: which open surveys move, and by how much. */
function ImpactPanel({
  impact,
  pending,
  onBack,
  onConfirm,
}: {
  impact: AccountImpact;
  pending: boolean;
  onBack: () => void;
  onConfirm: () => void;
}) {
  const { admin: t, common, jobFunction: fn, band: bandT } = useT();
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium text-ink">{t.previewTitle}</p>
      <p className="text-sm text-muted">
        {jobLabel(fn, bandT, impact.function_before, impact.band_before, "-")}
        {" → "}
        {jobLabel(fn, bandT, impact.function_after, impact.band_after, "-")}
      </p>
      {impact.may_author_before !== impact.may_author_after ? (
        <p className="text-sm text-warn-text">
          {impact.may_author_after ? t.previewNowAuthor : t.previewNowRespondent}
        </p>
      ) : null}
      {impact.surveys.length ? (
        <ul className="flex flex-col gap-2">
          {impact.surveys.map((survey) => (
            <li
              key={survey.template_id}
              className="rounded-lg border border-warn-border bg-warn-fill p-3"
            >
              <p className="text-sm font-medium text-warn-text">{survey.title}</p>
              <p className="text-xs text-warn-text">
                {t.previewReach(survey.reach_before, survey.reach_after)}
                {" · "}
                {survey.now_in ? t.previewGains : t.previewLoses}
              </p>
            </li>
          ))}
        </ul>
      ) : null}
      <DialogFooter>
        <Button variant="quiet" onClick={onBack} disabled={pending}>
          {t.back}
        </Button>
        <Button variant="primary" onClick={onConfirm} disabled={pending}>
          {pending ? common.saving : t.saveAnyway}
        </Button>
      </DialogFooter>
    </div>
  );
}
