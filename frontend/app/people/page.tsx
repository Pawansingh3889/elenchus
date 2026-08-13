"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { PersonDialog } from "@/components/PersonDialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { audienceLabel, departmentLabel } from "@/lib/audience";
import { useT } from "@/lib/i18n/useT";
import { useCurrentUser, useMe, usePeople } from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import type { Person } from "@/lib/types";

/**
 * Who is on the plant, and where they sit.
 *
 * It exists because a reach number was unreadable without it. A survey aimed at QA
 * reporting "1 of 2 answered" is correct and unexplainable when nothing on any screen
 * says who the two are, and one of them holds an author account because the senior
 * groups sign in with Teams.
 *
 * Read-only unless you administer the place, in which case this is also where accounts
 * are made and where it is decided what somebody is. Those controls hang off `useMe`
 * rather than off the role or the department in hand: half of `is_admin` is an email
 * allowlist that lives in server settings and is deliberately never sent to a browser,
 * so a page working it out locally would hide the controls from every administrator who
 * is not in the IT department.
 *
 * Hiding them is a courtesy, not the enforcement. `require_admin` guards both routes, so
 * a respondent who reaches this page with a crafted request is refused by the server.
 */
export default function People() {
  const { people, audience: aud, department, home, admin: t } = useT();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: rows, isLoading, error } = usePeople();
  const { data: me } = useMe();
  const router = useRouter();
  // `undefined` is "not open"; `null` is "open, creating". A person is "open, editing
  // them". One piece of state rather than two, so the dialog cannot be asked to create
  // and edit at once.
  const [editing, setEditing] = useState<Person | null | undefined>(undefined);

  // Author-only on the server too. Sending a respondent away rather than rendering the
  // 403 they would otherwise collect on arrival.
  const isRespondent = currentUser?.role === "respondent";
  useEffect(() => {
    if (isRespondent) router.replace("/respond");
  }, [isRespondent, router]);

  if (!currentUserId) return <p className="p-6 text-muted">{home.pickUser}</p>;
  if (isRespondent) return <p className="p-6 text-muted">{home.goingToRespond}</p>;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h1 className="text-md font-semibold text-ink">{people.title}</h1>
          <p className="text-sm text-muted">{people.subtitle}</p>
        </div>
        {me?.is_admin ? (
          <Button variant="primary" onClick={() => setEditing(null)}>
            {t.addPerson}
          </Button>
        ) : null}
      </div>

      {error ? <ErrorBanner error={error} /> : null}
      {isLoading ? <Skeleton className="h-64 w-full" /> : null}

      {rows ? (
        <Card className="overflow-x-auto p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{people.colName}</TableHead>
                <TableHead>{people.colRole}</TableHead>
                <TableHead>{people.colDepartment}</TableHead>
                <TableHead>{people.colGroups}</TableHead>
                {me?.is_admin ? <TableHead>{t.colActions}</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((person) => (
                <TableRow key={person.id}>
                  <TableCell className="font-medium text-ink">{person.display_name}</TableCell>
                  <TableCell className="text-muted">
                    {person.role === "author" ? people.roleAuthor : people.roleRespondent}
                    {/* `role` is stored as sent, so it can drift from the Entra id that
                        is meant to decide it. An author with no id builds surveys today
                        and cannot sign in the day that derivation is switched on, which
                        is invisible everywhere else. */}
                    {person.role === "author" && !person.has_microsoft_id ? (
                      <Badge variant="warn" className="ms-2" title={t.noEntraIdWhy}>
                        {t.noEntraId}
                      </Badge>
                    ) : null}
                  </TableCell>
                  <TableCell className="text-muted">
                    {person.department ? departmentLabel(department, person.department) : "-"}
                  </TableCell>
                  <TableCell>
                    {person.groups.length ? (
                      <span className="flex flex-wrap gap-1">
                        {/* Named through the same helper the picker and the publish
                            dialog use, so a group is called one thing everywhere. */}
                        {person.groups.map((g) => (
                          <Badge key={g}>{audienceLabel(aud, g)}</Badge>
                        ))}
                      </span>
                    ) : (
                      // A real state worth seeing rather than a blank cell: somebody in
                      // no group can be asked nothing at all, not even a survey aimed at
                      // everyone, and that is usually a mistake somebody should fix.
                      <span className="text-sm text-warn-text">{people.noGroups}</span>
                    )}
                  </TableCell>
                  {me?.is_admin ? (
                    <TableCell>
                      <Button variant="quiet" size="sm" onClick={() => setEditing(person)}>
                        {t.edit}
                      </Button>
                    </TableCell>
                  ) : null}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      ) : null}

      {/* Only for the people who cannot act on it. An administrator is looking at the
          controls, so telling them the page is read-only would be telling them something
          untrue. */}
      {me?.is_admin ? null : <p className="text-xs text-muted">{people.readOnly}</p>}

      {editing !== undefined ? (
        <PersonDialog person={editing} onClose={() => setEditing(undefined)} />
      ) : null}
    </div>
  );
}
