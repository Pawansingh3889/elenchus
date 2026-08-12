"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Badge } from "@/components/ui/badge";
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
import { useCurrentUser, usePeople } from "@/lib/queries";
import { useUserStore } from "@/lib/store";

/**
 * Who is on the plant, and where they sit.
 *
 * It exists because a reach number was unreadable without it. A survey aimed at QA
 * reporting "1 of 2 answered" is correct and unexplainable when nothing on any screen
 * says who the two are, and one of them holds an author account because the senior
 * groups sign in with Teams.
 *
 * Read-only on purpose. Membership comes from the seed until there is a screen to edit
 * it, and a page that showed an editable control which silently did nothing would be
 * worse than one that plainly reports.
 */
export default function People() {
  const { people, audience: aud, department, home } = useT();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: rows, isLoading, error } = usePeople();
  const router = useRouter();

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
      <div>
        <h1 className="text-md font-semibold text-ink">{people.title}</h1>
        <p className="text-sm text-muted">{people.subtitle}</p>
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
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((person) => (
                <TableRow key={person.id}>
                  <TableCell className="font-medium text-ink">{person.display_name}</TableCell>
                  <TableCell className="text-muted">
                    {person.role === "author" ? people.roleAuthor : people.roleRespondent}
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
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      ) : null}

      <p className="text-xs text-muted">{people.readOnly}</p>
    </div>
  );
}
