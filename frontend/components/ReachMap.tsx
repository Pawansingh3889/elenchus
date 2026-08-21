"use client";

import { useState } from "react";

import { Card } from "@/components/ui/card";
import { bandTint } from "@/lib/audience";
import { useT } from "@/lib/i18n/useT";
import { cn } from "@/lib/utils";
import type { Band, JobFunction, Person, SurveyAudience } from "@/lib/types";

/**
 * Who a survey reaches, drawn rather than described.
 *
 * The page said "who is on the plant, and which surveys can reach them" above a table of
 * jobs, which answers the first half and leaves the second to be worked out. This is the
 * second half: the org chart as a grid, function down and band across, with the audience
 * you pick lit up across it.
 *
 * A grid because the job model is already two axes, and every audience is a shape on
 * them: `operatives` is one cell, `qa` is a row, `managers` is everything right of a
 * line, `health_safety` is a function plus whoever carries the hat, and `everyone` is
 * the lot. Seeing the shape is the point; a list of names would say who without ever
 * saying why.
 *
 * **Membership is never computed here.** Each person arrives carrying the audiences that
 * reach them, decided by `app/access` on the server, which is the same call the
 * denominators use. Re-deriving it in the browser would be a paraphrase of the rules,
 * and a paraphrase drifts.
 */

// The axes, in the order the plant is organised rather than alphabetically: the floor
// first, then the functions that support it, then the office. Bands ascend left to
// right, which is also the direction authoring rights switch on.
const FUNCTIONS: JobFunction[] = [
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
const BANDS: Band[] = ["operative", "line_leader", "supervisor", "manager", "head", "director"];

// Every audience except `person`, which names one individual and is a property of a
// survey rather than of a job, so it has no shape on this grid.
const AUDIENCES: SurveyAudience[] = [
  "everyone",
  "operatives",
  "line_leaders",
  "supervisors",
  "shift_managers",
  "managers",
  "qa",
  "health_safety",
];

export function ReachMap({ people }: { people: Person[] }) {
  const { people: msg, audience: aud, band: bandMsg, jobFunction: fnMsg } = useT();
  const [selected, setSelected] = useState<SurveyAudience | null>(null);

  const inCell = (fn: JobFunction, band: Band) =>
    people.filter((p) => p.function === fn && p.band === band);
  const reached = selected ? people.filter((p) => p.audiences.includes(selected)) : [];
  // The gap between who the rules include and who could actually receive it. A survey
  // reaching twelve people is a different fact from twelve people being able to answer,
  // and while the floor has no way to sign in those two numbers must not be one number.
  const contactable = reached.filter((p) => p.has_microsoft_id);
  const unreachable = reached.filter((p) => !p.has_microsoft_id);

  // Rows with nobody in them are dropped: ten functions against six bands is sixty cells
  // and this plant fills eleven of them, so an empty grid would be mostly a grid.
  const rows = FUNCTIONS.filter((fn) => people.some((p) => p.function === fn));

  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-2 text-sm text-muted">
          {msg.mapLabel}
          <select
            className="field w-auto"
            value={selected ?? ""}
            onChange={(e) => setSelected((e.target.value || null) as SurveyAudience | null)}
          >
            <option value="">{msg.mapNoAudience}</option>
            {AUDIENCES.map((a) => (
              <option key={a} value={a}>
                {audienceName(aud, a)}
              </option>
            ))}
          </select>
        </label>
        {selected ? (
          <p className="text-sm">
            <b className="tabular-nums">{reached.length}</b>{" "}
            <span className="text-muted">{msg.mapReaches}</span>
            {unreachable.length > 0 ? (
              <span className="text-warn-text">
                {" · "}
                {msg.mapCannotReach(contactable.length, unreachable.length)}
              </span>
            ) : null}
          </p>
        ) : (
          <p className="text-sm text-muted">{msg.mapHint}</p>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="p-1 text-start text-xs font-semibold uppercase tracking-wide text-muted">
                {msg.colJob}
              </th>
              {BANDS.map((b) => (
                <th
                  key={b}
                  className="p-1 text-center text-xs font-semibold uppercase tracking-wide text-muted"
                >
                  {bandMsg[bandKey(b)]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((fn) => (
              <tr key={fn}>
                <th className="p-1 text-start font-medium text-ink">{fnMsg[functionKey(fn)]}</th>
                {BANDS.map((band) => {
                  const here = inCell(fn, band);
                  const lit = selected
                    ? here.filter((p) => p.audiences.includes(selected)).length
                    : 0;
                  return (
                    <td key={band} className="p-1 text-center">
                      {here.length === 0 ? (
                        // A dash, not a zero. Nobody holds this job; it is not a count
                        // that happens to be none.
                        <span className="text-muted-light">-</span>
                      ) : (
                        <span
                          className={cn(
                            // A hairline on every cell, so the ramp's first step has an
                            // edge: its fill is one shade off the card by construction, and
                            // a count floating on nothing reads as unstyled rather than as
                            // the lightest rung.
                            "inline-block min-w-7 rounded-md border border-line px-2 py-0.5 tabular-nums",
                            // Two things a cell can say, and they never share a colour.
                            // Its band, as a step on the neutral ramp, so seniority reads
                            // as depth across the row. And whether the chosen audience
                            // reaches it, in the accent blue, which on this page means
                            // that and nothing else. A cell that is both is lit, because
                            // the question the reader asked was "who is reached".
                            lit > 0 ? "bg-accent-strong font-semibold text-on-slab" : bandTint(band),
                            // Once an audience is picked, an unreached cell steps back so
                            // the reached ones are the figure and the rest the ground.
                            selected && lit === 0 && "opacity-45",
                          )}
                          // The cell says how many of the people in it the audience
                          // reaches, which is the whole question on a hatted function.
                          title={here.map((p) => p.display_name).join(", ")}
                        >
                          {selected ? `${lit}/${here.length}` : here.length}
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Named, not just counted. A number nobody can check is the thing this page was
          built to stop. */}
      {selected && unreachable.length > 0 ? (
        <p className="text-xs text-muted">
          {msg.mapUnreachableNames(unreachable.map((p) => p.display_name).join(", "))}
        </p>
      ) : null}
    </Card>
  );
}

/** The locale keys are camelCase where the values are snake_case. */
const functionKey = (fn: JobFunction) =>
  fn === "health_safety" ? "healthSafety" : fn === "supply_chain" ? "supplyChain" : fn;
const bandKey = (b: Band) => (b === "line_leader" ? "lineLeader" : b);
const audienceName = (aud: Record<string, unknown>, a: SurveyAudience) => {
  const key =
    a === "line_leaders"
      ? "lineLeaders"
      : a === "shift_managers"
        ? "shiftManagers"
        : a === "health_safety"
          ? "healthSafety"
          : a;
  return String(aud[key] ?? a);
};
