"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { PersonDialog } from "@/components/PersonDialog";
import { ReachMap } from "@/components/ReachMap";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Stat } from "@/components/Stat";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { bandLabel, bandTint, functionLabel, hatLabel } from "@/lib/audience";
import { SignInPrompt } from "@/components/SignInPrompt";
import { useT } from "@/lib/i18n/useT";
import { useAudienceReach, useCurrentUser, useMe, usePeople } from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { Band, JobFunction, Person } from "@/lib/types";

// The same axes the reach map draws, so the table under it reads in the same order.
const FUNCTION_ORDER: JobFunction[] = [
  "production",
  "quality",
  "health_safety",
  "technical",
  "planning",
  "supply_chain",
  "hr",
  "finance",
  "it",
  "executive",
];
const BAND_RANK: Band[] = ["operative", "line_leader", "supervisor", "manager", "head", "director"];

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
  const { people, jobFunction: fn, band, hat, home, admin: t } = useT();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const currentUser = useCurrentUser();
  const { data: rows, isLoading, error } = usePeople();
  const { data: me } = useMe();
  const router = useRouter();
  // `undefined` is "not open"; `null` is "open, creating". A person is "open, editing
  // them". One piece of state rather than two, so the dialog cannot be asked to create
  // and edit at once.
  const [editing, setEditing] = useState<Person | null | undefined>(undefined);
  const [query, setQuery] = useState("");
  const [bandFilter, setBandFilter] = useState<Band | "">("");

  // The list, narrowed and grouped. Grouped by function because that is how the plant
  // reads its own org chart and how the map above is drawn; senior first within a group,
  // director down to operative, then by name, so the order under each heading is the
  // order the ramp above it runs. Alphabetical across five hundred people was a list you
  // could only scroll, and search is the difference between a directory and a printout.
  const grouped = useMemo(() => {
    const q = query.trim().toLowerCase();
    const shown = (rows ?? []).filter((person) => {
      if (bandFilter && person.band !== bandFilter) return false;
      if (!q) return true;
      return person.display_name.toLowerCase().includes(q);
    });
    const byFunction = new Map<JobFunction | null, Person[]>();
    for (const person of shown) {
      const key = person.function ?? null;
      const list = byFunction.get(key) ?? [];
      list.push(person);
      byFunction.set(key, list);
    }
    for (const list of byFunction.values()) {
      list.sort((a, b) => {
        const ra = a.band ? BAND_RANK.indexOf(a.band) : -1;
        const rb = b.band ? BAND_RANK.indexOf(b.band) : -1;
        if (ra !== rb) return rb - ra;
        return a.display_name.localeCompare(b.display_name);
      });
    }
    // Functions in the plant's own order, the floor first, then whoever has no job at
    // the end: an account with no job is a state worth seeing, and seeing last.
    const order: (JobFunction | null)[] = [...FUNCTION_ORDER, null];
    return {
      shown: shown.length,
      total: rows?.length ?? 0,
      groups: order
        .filter((fn) => byFunction.has(fn))
        .map((fn) => ({ fn, people: byFunction.get(fn) as Person[] })),
    };
  }, [rows, query, bandFilter]);

  // Author-only on the server too. Sending a non-authoring caller away rather than
  // rendering the 403 they would otherwise collect on arrival.
  const isRespondent = currentUser ? !currentUser.may_author : false;

  // Audience reach for the summary cards
  const { data: audienceReach } = useAudienceReach(true);

  // Compute summary stats from rows and audienceReach
  const summary = useMemo(() => {
    if (!rows) return null;
    const totalPeople = rows.length;
    const authors = rows.filter((p) => p.may_author).length;
    const admins = rows.filter((p) => p.function === "it").length; // IT function grants admin
    const noJob = rows.filter((p) => !p.function || !p.band).length;
    const byFunction = new Map<JobFunction | null, number>();
    const byBand = new Map<Band, number>();
    const reachTotal = audienceReach ? Object.values(audienceReach).reduce((a, b) => a + b, 0) : 0;
    
    for (const person of rows) {
      // By function
      const fnKey = person.function ?? null;
      byFunction.set(fnKey, (byFunction.get(fnKey) ?? 0) + 1);
      // By band
      if (person.band) {
        byBand.set(person.band, (byBand.get(person.band) ?? 0) + 1);
      }
    }
    
    return {
      totalPeople,
      authors,
      admins,
      noJob,
      byFunction,
      byBand,
      reachTotal,
      audienceReach: audienceReach ?? {},
    };
  }, [rows, audienceReach]);

  useEffect(() => {
    if (isRespondent) router.replace("/respond");
  }, [isRespondent, router]);

  if (!currentUserId) return <SignInPrompt />;
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

      {/* Summary cards at the top */}
      {summary && (
        <section className="flex flex-col gap-4">
          <h2 className="text-md font-semibold text-ink">{people.summaryTitle}</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="p-4 flex flex-col gap-1">
              <Stat value={summary.totalPeople} label={people.summaryTotal} />
            </Card>
            <Card className="p-4 flex flex-col gap-1">
              <Stat value={summary.authors} label={people.summaryAuthors} />
            </Card>
            <Card className="p-4 flex flex-col gap-1">
              <Stat value={summary.admins} label={people.summaryAdmins} />
            </Card>
            <Card className="p-4 flex flex-col gap-1">
              <Stat value={summary.noJob} label={people.summaryNoJob} />
            </Card>
          </div>
          
          {/* By function */}
          <Card className="p-4 flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-ink">{people.summaryByFunction}</h3>
            <div className="flex flex-wrap gap-2">
              {FUNCTION_ORDER.map((func) => {
                const count = summary.byFunction.get(func) ?? 0;
                return count > 0 ? (
                  <Badge key={func} variant="outline" className="text-xs">
                    {functionLabel(fn, func)}: {count}
                  </Badge>
                ) : null;
              })}
              {summary.byFunction.has(null) && (
                <Badge key="none" variant="outline" className="text-xs text-warn-text">
                  {people.noJob}: {summary.byFunction.get(null)}
                </Badge>
              )}
            </div>
          </Card>

          {/* By band */}
          <Card className="p-4 flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-ink">{people.summaryByBand}</h3>
            <div className="flex flex-wrap gap-2">
              {BAND_RANK.map((b) => {
                const count = summary.byBand.get(b) ?? 0;
                return count > 0 ? (
                  <Badge key={b} variant="outline" className={cn("text-xs", bandTint(b))}>
                    {bandLabel(band, b)}: {count}
                  </Badge>
                ) : null;
              })}
            </div>
          </Card>

          {/* Audience reach */}
          <Card className="p-4 flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-ink">{people.summaryAudienceReach}</h3>
            <div className="flex flex-wrap gap-2">
              {(Object.entries(summary.audienceReach) as [string, number][]).map(([audKey, count]) => (
                <Badge key={audKey} variant="outline" className="text-xs">
                  {audKey}: {count}
                </Badge>
              ))}
              <Badge variant="accent" className="text-xs">
                {people.summaryReachTotal}: {summary.reachTotal}
              </Badge>
            </div>
          </Card>
        </section>
      )}

      {rows ? (
        <Card className="overflow-x-auto p-0">
          <ReachMap people={rows ?? []} />

          {/* Find someone. A search box and a band filter, above the table they narrow
              and below the map they do not touch: the map is the whole plant by
              definition, and narrowing it would draw an audience that does not exist. */}
          <div className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3">
            <input
              type="search"
              className="field"
              // Width inline rather than a utility: `.field` in globals.css is unlayered
              // and sets `width: 100%`, which beats any `w-*` whatever the layer. An
              // inline style is the one thing that beats an unlayered rule.
              style={{ width: "14rem" }}
              placeholder={people.searchPlaceholder}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label={people.searchPlaceholder}
            />
            <label className="flex items-center gap-2 text-sm text-muted">
              {people.bandFilterLabel}
              <select
                className="field w-auto"
                value={bandFilter}
                onChange={(e) => setBandFilter(e.target.value as Band | "")}
              >
                <option value="">{people.bandFilterAll}</option>
                {BAND_RANK.map((b) => (
                  <option key={b} value={b}>
                    {bandLabel(band, b)}
                  </option>
                ))}
              </select>
            </label>
            {query || bandFilter ? (
              <span className="text-sm text-muted">
                {people.showing(grouped.shown, grouped.total)}
              </span>
            ) : null}
          </div>

          {grouped.groups.length === 0 ? (
            <p className="p-4 text-sm text-muted">{people.noMatches}</p>
          ) : null}

          {grouped.groups.map(({ fn: groupFn, people: members }) => (
            <section key={groupFn ?? "none"} className="border-b border-line last:border-b-0">
              <div className="flex items-center gap-2 bg-surface px-4 py-2">
                <h2 className="text-xs font-semibold uppercase tracking-wide text-muted">
                  {groupFn ? functionLabel(fn, groupFn) : people.noJob}
                </h2>
                <span className="text-xs text-muted">{people.inFunction(members.length)}</span>
              </div>
              <Table>
                <TableHeader className="sr-only">
                  <TableRow>
                    <TableHead>{people.colName}</TableHead>
                    <TableHead>{people.colJob}</TableHead>
                    <TableHead>{people.colHats}</TableHead>
                    {me?.is_admin ? <TableHead>{t.colActions}</TableHead> : null}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {members.map((person) => (
                    <TableRow
                      key={person.id}
                      // The whole row opens the person for an administrator, not the small
                      // button at its end. A row you have to aim at is a row that gets
                      // missed, and there is nothing else a click on it could mean.
                      className={cn(me?.is_admin && "cursor-pointer")}
                      onClick={me?.is_admin ? () => setEditing(person) : undefined}
                    >
                      <TableCell className="font-medium text-ink">{person.display_name}</TableCell>
                      <TableCell className="text-muted">
                        {person.function && person.band ? (
                          <span className="flex flex-wrap items-center gap-2">
                            {/* The band as a step on the same ramp the map uses, so a
                                person's tint here matches their cell up there. The
                                function is the group heading, so it is not repeated. */}
                            <span
                              className={cn(
                                "rounded-md px-2 py-0.5 text-xs font-medium",
                                bandTint(person.band),
                              )}
                            >
                              {bandLabel(band, person.band)}
                            </span>
                            {/* Derived on the server: the band decides authoring, and the
                                page just says so beside the job. */}
                            {person.may_author ? <Badge>{people.buildsSurveys}</Badge> : null}
                            {/* Somebody at an authoring band with no Entra id builds
                                surveys today and has no way to sign in when the header
                                shim is replaced, which is invisible everywhere else. */}
                            {person.may_author && !person.has_microsoft_id ? (
                              <Badge variant="warn" title={t.noEntraIdWhy}>
                                {t.noEntraId}
                              </Badge>
                            ) : null}
                          </span>
                        ) : (
                          // A real state worth seeing rather than a blank cell: an account
                          // with no job can be asked nothing at all, not even a survey
                          // aimed at everyone. Right for a service account, a mistake for
                          // a person, and this line is how the mistake gets seen.
                          <span className="text-sm text-warn-text">{people.noJob}</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {person.hats.length ? (
                          <span className="flex flex-wrap gap-1">
                            {person.hats.map((h) => (
                              <Badge key={h}>{hatLabel(hat, h)}</Badge>
                            ))}
                          </span>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </TableCell>
                      {me?.is_admin ? (
                        <TableCell>
                          {/* Kept beside the row click, for a keyboard: a row is not a
                              focusable thing, and this is. */}
                          <Button
                            variant="quiet"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditing(person);
                            }}
                          >
                            {t.edit}
                          </Button>
                        </TableCell>
                      ) : null}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </section>
          ))}
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
