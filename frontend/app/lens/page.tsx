"use client";

import { useRouter } from "next/navigation";

import { ErrorBanner } from "@/components/ErrorBanner";
import { LensStripView } from "@/components/lens/LensStripView";
import { dollars, milliseconds, moment, tokenCount } from "@/lib/lensFormat";
import { useLensRuns, useLensStrip, useMe } from "@/lib/queries";

/**
 * The lens: every traced run and what its model calls cost.
 *
 * Administrators only. The server refuses these reads to anyone else, and asking it who
 * is an administrator is the only honest check, because half of that answer is an email
 * allowlist the browser never sees.
 */
export default function LensHome() {
  const router = useRouter();
  const { data: me, isLoading: meLoading } = useMe();
  const admin = me?.is_admin === true;
  const strip = useLensStrip(admin);
  const runs = useLensRuns(admin);

  if (meLoading) return <p className="empty">Loading…</p>;
  if (!admin) return <p className="empty">Sign in as an administrator to use the lens.</p>;

  return (
    <div className="page lens">
      <div className="page-head">
        <h1>Lens</h1>
      </div>
      <p className="lens-provenance">
        Measured from the trace. Nothing on this page is estimated: a figure a provider did
        not report reads &ldquo;not reported&rdquo;, and a sum over such calls reads &ldquo;at
        least&rdquo;.
      </p>

      <ErrorBanner error={strip.error ?? runs.error} />
      {strip.data ? <LensStripView strip={strip.data} /> : null}

      <section className="lens-section">
        <h2 className="lens-heading">Traced runs</h2>
        <div className="lens-table-wrap">
          <table className="lens-table">
            <thead>
              <tr>
                <th>Survey</th>
                <th>Last turn</th>
                <th className="num">Turns</th>
                <th className="num">Attempts (failed)</th>
                <th className="num">Retries</th>
                <th className="num">Tokens in / out</th>
                <th className="num">Cost</th>
                <th className="num">Waited</th>
                <th className="num">First token p50</th>
              </tr>
            </thead>
            <tbody>
              {runs.data?.map((run) => (
                <tr
                  key={run.run_id}
                  className="lens-row-link"
                  onClick={() => router.push(`/lens/runs/${run.run_id}`)}
                >
                  <td>
                    <a href={`/lens/runs/${run.run_id}`}>{run.survey_title}</a>
                  </td>
                  <td>{moment(run.last_traced_at)}</td>
                  <td className="num">{run.turns}</td>
                  <td className="num">
                    {run.attempts} ({run.failed_attempts})
                  </td>
                  <td className="num">{run.retries}</td>
                  <td className="num">
                    {tokenCount(run.prompt_tokens, run.unmetered_attempts)} /{" "}
                    {tokenCount(run.completion_tokens, run.unmetered_attempts)}
                  </td>
                  <td className="num">{dollars(run.cost_usd, run.unmetered_attempts)}</td>
                  <td className="num">{milliseconds(run.turn_ms)}</td>
                  <td className="num">{milliseconds(run.first_token_ms_p50)}</td>
                </tr>
              ))}
              {runs.data && runs.data.length === 0 ? (
                <tr>
                  <td colSpan={9} className="muted">
                    No traced runs yet. Every survey turn taken from now on appears here.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
