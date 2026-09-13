"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useLensScope } from "@/lib/lensScope";
import { useLensRuns, useMe } from "@/lib/queries";

// `filtered` marks the pages the survey and run filter scopes. The overview has its own
// run list, the comparison picks its own two runs, and prompts are not about runs at all.
const FACTORS = [
  { href: "/lens", label: "Overview", filtered: false },
  { href: "/lens/inference", label: "Inference", filtered: true },
  { href: "/lens/state", label: "State", filtered: true },
  { href: "/lens/tools", label: "Tool selection", filtered: true },
  { href: "/lens/validation", label: "Validation", filtered: true },
  { href: "/lens/relationships", label: "Relationships", filtered: true },
  { href: "/lens/chains", label: "Cause chains", filtered: true },
  { href: "/lens/embeddings", label: "Embeddings", filtered: true },
  { href: "/lens/compare", label: "Compare runs", filtered: false },
  { href: "/lens/prompts", label: "Prompts", filtered: false },
] as const;

/**
 * The lens tabs and, on the factor pages, the one filter row that scopes everything
 * below it. Hidden from anyone the server does not call an administrator; the pages
 * themselves say why.
 */
export function LensNav() {
  const pathname = usePathname();
  const { data: me } = useMe();
  const admin = me?.is_admin === true;
  const runs = useLensRuns(admin);
  const [scope, setScope] = useLensScope();

  if (!admin) return null;
  const onFactor = FACTORS.some((f) => f.filtered && pathname.startsWith(f.href));
  const query = new URLSearchParams();
  if (scope.surveyId) query.set("survey", scope.surveyId);
  if (scope.runId) query.set("run", scope.runId);
  const suffix = query.toString() ? `?${query.toString()}` : "";

  const surveys = new Map<string, string>();
  for (const run of runs.data ?? []) surveys.set(run.template_id, run.survey_title);
  const runsInSurvey = (runs.data ?? []).filter(
    (run) => !scope.surveyId || run.template_id === scope.surveyId,
  );

  return (
    <div className="lens-nav">
      <nav className="lens-tabs" aria-label="Lens pages">
        {FACTORS.map((factor) => {
          const current =
            factor.href === "/lens" ? pathname === "/lens" : pathname.startsWith(factor.href);
          return (
            <Link
              key={factor.href}
              href={factor.filtered ? `${factor.href}${suffix}` : factor.href}
              className={current ? "lens-tab lens-tab-current" : "lens-tab"}
              aria-current={current ? "page" : undefined}
            >
              {factor.label}
            </Link>
          );
        })}
      </nav>
      {onFactor ? (
        <div className="lens-filters">
          <label className="lens-filter">
            <span>Survey</span>
            <select
              value={scope.surveyId ?? ""}
              onChange={(e) => setScope({ surveyId: e.target.value || null, runId: null })}
            >
              <option value="">All traced surveys</option>
              {[...surveys].map(([id, title]) => (
                <option key={id} value={id}>
                  {title}
                </option>
              ))}
            </select>
          </label>
          <label className="lens-filter">
            <span>Run</span>
            <select
              value={scope.runId ?? ""}
              onChange={(e) => setScope({ surveyId: scope.surveyId, runId: e.target.value || null })}
            >
              <option value="">All runs</option>
              {runsInSurvey.map((run) => (
                <option key={run.run_id} value={run.run_id}>
                  {run.survey_title} · {run.turns} turns · {run.run_id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}
    </div>
  );
}
