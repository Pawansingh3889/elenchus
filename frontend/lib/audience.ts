import type { Messages } from "./i18n/en";
import type { Band, Hat, JobFunction, SurveyAudience } from "./types";
import { cn } from "./utils";

/**
 * What to call an audience, in one place.
 *
 * The picker on the landing page and the publish confirmation both have to name who a
 * survey is for, and two copies of the mapping is two places for a new audience to be
 * half-added. An exhaustive `switch` over the union is what makes that a compile error
 * rather than a silent gap: add a value to `SurveyAudience` and this stops type-checking,
 * which is the frontend's version of the backend's audience completeness test.
 *
 * `personName` is the display name when the survey names somebody. It falls back to the
 * generic "one person" rather than rendering an id or an empty string, because the user
 * list may not have arrived yet and a blank is worse than a vaguer truth.
 */
export function audienceLabel(
  aud: Messages["audience"],
  audience: SurveyAudience,
  personName?: string | null,
): string {
  switch (audience) {
    case "everyone":
      return aud.everyone;
    case "operatives":
      return aud.operatives;
    case "line_leaders":
      return aud.lineLeaders;
    case "supervisors":
      return aud.supervisors;
    case "shift_managers":
      return aud.shiftManagers;
    case "managers":
      return aud.managers;
    case "qa":
      return aud.qa;
    case "health_safety":
      return aud.healthSafety;
    case "person":
      return personName || aud.person;
  }
}

/**
 * What to call a function. Same exhaustive-switch trick as above, for the same reason.
 *
 * Functions, bands and audiences are deliberately separate vocabularies answering
 * separate questions, so they get separate label helpers rather than one that takes a
 * union of all three and cannot say which it was handed.
 */
export function functionLabel(fn: Messages["jobFunction"], value: JobFunction): string {
  switch (value) {
    case "production":
      return fn.production;
    case "quality":
      return fn.quality;
    case "health_safety":
      return fn.healthSafety;
    case "technical":
      return fn.technical;
    case "planning":
      return fn.planning;
    case "hr":
      return fn.hr;
    case "finance":
      return fn.finance;
    case "supply_chain":
      return fn.supplyChain;
    case "it":
      return fn.it;
    case "executive":
      return fn.executive;
  }
}

/** What to call a band. The floor's own words, so `line_leader` and friends read as
 *  job titles rather than access tiers. */
export function bandLabel(band: Messages["band"], value: Band): string {
  switch (value) {
    case "operative":
      return band.operative;
    case "line_leader":
      return band.lineLeader;
    case "supervisor":
      return band.supervisor;
    case "manager":
      return band.manager;
    case "head":
      return band.head;
    case "director":
      return band.director;
  }
}

/**
 * The step of the band ramp a band paints with, as the two Tailwind classes for it.
 *
 * Bands are ordered, so they take an ordered scale: six lightness steps from operative to
 * director, defined as `--band-N` and `--on-band-N` in globals.css and measured there.
 * One place turns a band into its classes so the reach map and the person table cannot
 * tint the same band two different ways. Each pair goes through `cn()` rather than being
 * returned as a bare string, and that is not decoration: the class guard reads the
 * argument lists of `cn()` and `className=` and nothing else, so a bare `return "bg-…"`
 * here would be a class the guard never sees. Planted a `text-on-band-99` to check, and
 * the bare form passed; the `cn()` form is rejected. A `bg-band-${n}` template would be
 * invisible for the same reason.
 *
 * Exhaustive over the union for the same reason `bandLabel` is: a seventh band added to
 * `Band` stops this compiling rather than rendering untinted.
 */
export function bandTint(value: Band): string {
  switch (value) {
    case "operative":
      return cn("bg-band-1", "text-on-band-1");
    case "line_leader":
      return cn("bg-band-2", "text-on-band-2");
    case "supervisor":
      return cn("bg-band-3", "text-on-band-3");
    case "manager":
      return cn("bg-band-4", "text-on-band-4");
    case "head":
      return cn("bg-band-5", "text-on-band-5");
    case "director":
      return cn("bg-band-6", "text-on-band-6");
  }
}

/** What to call a hat: the responsibility itself, not the H&S function's name, so a
 *  supervisor's badge reads as a duty carried rather than a second job. */
export function hatLabel(hat: Messages["hat"], value: Hat): string {
  switch (value) {
    case "health_safety":
      return hat.healthSafety;
  }
}

/** One person's job as a single line: "Production · Shift manager", or the service
 *  account fallback when there is no job to name. */
export function jobLabel(
  fn: Messages["jobFunction"],
  band: Messages["band"],
  functionValue: JobFunction | null,
  bandValue: Band | null,
  noJob: string,
): string {
  if (functionValue === null || bandValue === null) return noJob;
  return `${functionLabel(fn, functionValue)} · ${bandLabel(band, bandValue)}`;
}
