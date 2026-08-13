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
import { audienceLabel, departmentLabel } from "@/lib/audience";
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
  CreatorDepartment,
  Person,
  RespondentGroup,
  UserRole,
} from "@/lib/types";

const DEPARTMENTS: CreatorDepartment[] = [
  "hr",
  "finance",
  "technical",
  "management",
  "quality",
  "it",
];
const GROUPS: RespondentGroup[] = [
  "operatives",
  "line_leaders",
  "supervisors",
  "shift_managers",
  "managers",
  "qa",
];

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
 * The rules about which combinations are allowed are deliberately NOT duplicated here.
 * `role`, `department` and `groups` constrain each other in ways that matter for access
 * (a respondent holding a department would be read as a colleague, and colleagues read
 * raw answers), and a second copy of that logic in a browser is a copy that drifts from
 * the one the database is actually protected by. So the form submits, and the server's
 * sentence is what the author reads. What the form does do is make the valid shape the
 * easy one to reach: choosing an account type shows the field that type needs.
 */
export function PersonDialog({ person, onClose }: Props) {
  const { admin: t, common, audience: aud, department: dep, people } = useT();
  const locale = useLocaleStore((s) => s.locale);
  const create = useCreateAccount();
  const replace = useReplaceAccount();
  const preview = usePreviewAccount();
  const { data: history } = useAccountHistory(person?.id ?? null);

  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState(person?.display_name ?? "");
  const [role, setRole] = useState<UserRole>(person?.role ?? "respondent");
  const [department, setDepartment] = useState<CreatorDepartment | null>(
    person?.department ?? null,
  );
  const [groups, setGroups] = useState<RespondentGroup[]>(person?.groups ?? []);
  // The id itself is never sent to the browser, only whether one is set, so an edit
  // starts blank and a blank submit clears it. Said plainly under the field rather than
  // left for somebody to discover by saving.
  const [microsoftId, setMicrosoftId] = useState("");
  // The guardrail step. Saving an edit asks the server what would change first; when
  // open surveys are affected or the account type flips, the answer is shown and Save
  // becomes a decision rather than a reflex. The form is hidden meanwhile, which is
  // what lets `buildBody()` be called again on confirm and mean the same edit.
  const [impact, setImpact] = useState<AccountImpact | null>(null);

  const pending = create.isPending || replace.isPending || preview.isPending;
  const error = create.error ?? replace.error ?? preview.error;

  function toggleGroup(group: RespondentGroup) {
    setGroups((current) =>
      current.includes(group) ? current.filter((g) => g !== group) : [...current, group],
    );
  }

  function buildBody(): AccountWrite {
    return {
      display_name: displayName,
      role,
      // An empty box is an absent id, not an empty one. The server folds this too; doing
      // it here as well keeps the request honest about what it is asking for.
      microsoft_id: microsoftId.trim() || null,
      // Carried only for the type that has one. Leaving a stale department on an account
      // switched to respondent is exactly the state the server refuses, and sending it
      // would turn a tidy form into a confusing 422.
      department: role === "author" ? department : null,
      groups,
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
    // answer would surprise: reach moving on an open survey, or the account type
    // changing what this person can do.
    if (!person) {
      save();
      return;
    }
    preview.mutate(
      { id: person.id, data: buildBody() },
      {
        onSuccess: (result) => {
          if (result.surveys.length > 0 || result.role_before !== result.role_after) {
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

          <fieldset className="flex flex-col gap-1">
            <legend className="text-sm font-medium text-ink">{t.roleLabel}</legend>
            {(["respondent", "author"] as UserRole[]).map((option) => (
              <label key={option} className="flex items-start gap-2 text-sm text-ink">
                <input
                  type="radio"
                  name="role"
                  className="mt-1"
                  checked={role === option}
                  onChange={() => setRole(option)}
                />
                <span>
                  {option === "author" ? people.roleAuthor : people.roleRespondent}
                  <span className="block text-xs text-muted">
                    {option === "author" ? t.roleAuthorHint : t.roleRespondentHint}
                  </span>
                </span>
              </label>
            ))}
          </fieldset>

          {role === "author" ? (
            <label className="flex flex-col gap-1">
              <span className="text-sm font-medium text-ink">{t.departmentLabel}</span>
              <select
                className={FIELD}
                value={department ?? ""}
                onChange={(e) =>
                  setDepartment((e.target.value || null) as CreatorDepartment | null)
                }
              >
                <option value="">{t.departmentNone}</option>
                {DEPARTMENTS.map((d) => (
                  <option key={d} value={d}>
                    {departmentLabel(dep, d)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          <fieldset className="flex flex-col gap-1">
            <legend className="text-sm font-medium text-ink">{t.groupsLabel}</legend>
            <span className="text-xs text-muted">{t.groupsHint}</span>
            <div className="flex flex-wrap gap-3 pt-1">
              {GROUPS.map((group) => (
                <label key={group} className="flex items-center gap-2 text-sm text-ink">
                  <input
                    type="checkbox"
                    checked={groups.includes(group)}
                    onChange={() => toggleGroup(group)}
                  />
                  {audienceLabel(aud, group)}
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
                    {changeSummary(entry, t, aud, people)}
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

/** One audit row as a sentence fragment: what changed, in the reader's language. */
function changeSummary(
  entry: AccountChangeEntry,
  t: Messages["admin"],
  aud: Messages["audience"],
  people: Messages["people"],
): string {
  if (entry.kind === "created" || entry.before === null) return t.historyCreated;
  const { before, after } = entry;
  const parts: string[] = [];
  const added = after.groups.filter((g) => !before.groups.includes(g));
  const removed = before.groups.filter((g) => !after.groups.includes(g));
  if (added.length) parts.push(t.historyAdded(added.map((g) => audienceLabel(aud, g)).join(", ")));
  if (removed.length) {
    parts.push(t.historyRemoved(removed.map((g) => audienceLabel(aud, g)).join(", ")));
  }
  if (before.role !== after.role) {
    parts.push(t.historyRole(after.role === "author" ? people.roleAuthor : people.roleRespondent));
  }
  if (
    before.display_name !== after.display_name ||
    before.department !== after.department ||
    before.microsoft_id !== after.microsoft_id
  ) {
    parts.push(t.historyOther);
  }
  // A row exists because something differed, so parts cannot be empty; joined rather
  // than listed so the line stays a line.
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
  const { admin: t, common } = useT();
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium text-ink">{t.previewTitle}</p>
      {impact.role_before !== impact.role_after ? (
        <p className="text-sm text-warn-text">
          {impact.role_after === "author" ? t.previewNowAuthor : t.previewNowRespondent}
        </p>
      ) : null}
      {impact.surveys.length ? (
        <ul className="flex flex-col gap-2">
          {impact.surveys.map((survey) => (
            <li key={survey.template_id} className="rounded-lg border border-warn-border bg-warn-fill p-3">
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
