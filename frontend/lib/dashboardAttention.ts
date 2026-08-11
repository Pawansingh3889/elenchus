import type { DashboardRow } from "./types";

/**
 * Why a survey wants the author's attention, or null if it is simply running.
 *
 * The dashboard used to sort by recency and give every row the same weight, so a survey
 * nobody had answered and one everybody had looked identical: same size, same pill, same
 * two buttons. The number an author actually opens the page for is "which of these needs
 * me", and it was the one thing the page did not say.
 */
export type Attention =
  | "resultsReady" // everyone it was aimed at has answered
  | "nobodyYet" // published, and not one person has finished
  | "stalled" // people started and none of them got to the end
  | "notPublished"; // a draft, so nobody can answer it at all

/** Most useful first. A survey with answers waiting is the one worth opening today;
 *  an unfinished draft has waited this long and can wait until after. */
const ORDER: Attention[] = ["resultsReady", "nobodyYet", "stalled", "notPublished"];

export function attentionOf(row: DashboardRow): Attention | null {
  if (row.status === "draft") return "notPublished";
  // Closed surveys are finished work, not work outstanding. They get their own quiet
  // group rather than a nag: nothing about them is actionable.
  if (row.status !== "published") return null;
  if (row.people_completed === 0) return row.in_progress > 0 ? "stalled" : "nobodyYet";
  if (row.reach > 0 && row.people_completed >= row.reach) return "resultsReady";
  return null;
}

export interface Grouped {
  needsYou: { row: DashboardRow; why: Attention }[];
  running: DashboardRow[];
  closed: DashboardRow[];
}

export function groupForDashboard(rows: DashboardRow[]): Grouped {
  const needsYou: { row: DashboardRow; why: Attention }[] = [];
  const running: DashboardRow[] = [];
  const closed: DashboardRow[] = [];

  for (const row of rows) {
    if (row.status === "closed" || row.status === "archived") {
      closed.push(row);
      continue;
    }
    const why = attentionOf(row);
    if (why) needsYou.push({ row, why });
    else running.push(row);
  }

  needsYou.sort((a, b) => ORDER.indexOf(a.why) - ORDER.indexOf(b.why));
  // Running stays in the order the API sent, which is the author's own recency. Sorting
  // it by response rate would put the survey doing worst at the top of the group headed
  // "running", which reads as a second list of problems.
  return { needsYou, running, closed };
}
