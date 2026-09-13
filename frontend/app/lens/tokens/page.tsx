"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { ChosenReading, InterpAsks } from "@/components/lens/InterpAsks";
import { Tile } from "@/components/lens/LensStripView";
import { byGroup, GROUPS, groupsOf, probability, visible } from "@/lib/interpFormat";
import { dollars, milliseconds } from "@/lib/lensFormat";
import { useSelectedAsk } from "@/lib/lensScope";
import { useInterpAnalysis, useMe } from "@/lib/queries";
import type { StoredAnalysis } from "@/lib/schemas";

// A word mixes further from the neutral midpoint the harder it pulls; past this strength
// its text switches to the colour that stays readable on a strong fill.
const STRONG = 0.55;

/**
 * Token relationships: which parts of the prompt, and which words the respondent typed,
 * moved Qwen3-0.6B toward or away from the tool the hosted model called.
 */
export default function TokensPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [selected] = useSelectedAsk();
  const analysis = useInterpAnalysis(selected, admin);

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Token relationships</h1>
        </div>
        <p className="lens-provenance">
          Gradient times input, on Qwen3-0.6B reading the exact prompt a hosted call was sent: for
          every token, how much it moved the probability of writing the tool the hosted model
          called. Positive pushes toward that tool and negative away. Shares are of the total
          absolute pull, so the parts add to one. It explains how a small open model reads the
          prompt, never the hosted model&rsquo;s choice.
        </p>
        <InterpAsks admin={admin} need="attribution" />
        <ErrorBanner error={analysis.error} />
        <ChosenReading selected={selected} loading={analysis.isFetching} stored={analysis.data}>
          {(stored) =>
            stored.attribution === null ? (
              <p className="lens-note">
                This call has been read but not attributed. Attribute it above; on a laptop CPU
                it takes several times as long as the reading.
              </p>
            ) : (
              <Relationships stored={stored} />
            )
          }
        </ChosenReading>
      </div>
    </Gate>
  );
}

function Relationships({ stored }: { stored: StoredAnalysis }) {
  if (stored.attribution === null) return null;
  const attribution = stored.attribution.result.attribution;
  const groups = groupsOf(stored.analysis.sections);
  const toward = byGroup(
    Object.fromEntries(Object.entries(attribution.sections).map(([key, value]) => [key, value.positive])),
    groups,
  );
  const away = byGroup(
    Object.fromEntries(Object.entries(attribution.sections).map(([key, value]) => [key, value.negative])),
    groups,
  );
  const rows = GROUPS.map((group) => ({ part: group.label, toward: toward[group.key], away: away[group.key] }));
  const reach = Math.max(0.05, ...rows.map((row) => Math.max(row.toward, -row.away)));
  const onTarget = stored.analysis.tools.find((tool) => tool.name === attribution.target)?.probability ?? null;
  const labels = new Map(stored.analysis.sections.map((section) => [section.key, section.label]));
  const strongest = Math.max(1e-12, ...attribution.respondent_words.map((word) => Math.abs(word.score)));

  return (
    <>
      <div className="lens-tiles">
        <Tile label="Explains the pick" value={attribution.target} />
        <Tile label="Qwen on that pick" value={probability(onTarget)} />
        <Tile label="Attribution took" value={milliseconds(stored.attribution.duration_ms)} />
        <Tile label="Attribution cost" value={dollars(stored.attribution.cost_usd)} />
        <Tile label="Reading took" value={milliseconds(stored.duration_ms)} />
        <Tile
          label="The hosted call"
          value={`${milliseconds(stored.hosted_ms)} · ${dollars(stored.hosted_cost_usd)}`}
        />
      </div>

      <ChartCard
        title="Pull toward and away from the pick, per part of the prompt"
        sample={`${stored.analysis.prompt_tokens} prompt tokens; shares of the total absolute pull`}
        legend={[
          { label: "Toward the pick", color: "var(--div-pos)" },
          { label: "Away from it", color: "var(--div-neg)" },
        ]}
        table={<PartTable rows={rows} />}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} layout="vertical" stackOffset="sign" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid stroke="var(--border)" horizontal={false} />
            <XAxis type="number" domain={[-reach, reach]} ticks={[-reach, -reach / 2, 0, reach / 2, reach]} {...axis} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} />
            <YAxis type="category" dataKey="part" {...axis} width={170} />
            <Tooltip
              cursor={{ fill: "var(--highlight-soft)" }}
              content={(props) => <LensTooltip {...props} hideZero format={(v) => probability(Math.abs(v))} />}
            />
            <ReferenceLine x={0} stroke="var(--ink)" />
            <Bar isAnimationActive={false} dataKey="toward" name="Toward the pick" stackId="pull" fill="var(--div-pos)" maxBarSize={20} />
            <Bar isAnimationActive={false} dataKey="away" name="Away from it" stackId="pull" fill="var(--div-neg)" maxBarSize={20} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <section className="lens-section">
        <h2 className="lens-heading">What the respondent last said, word by word</h2>
        <p className="lens-note">
          Blue pushes toward the pick, orange away, and the stronger the colour the harder the
          pull, relative to the strongest word in this message.
        </p>
        <p className="lens-words">
          {attribution.respondent_words.map((word, index) => {
            const strength = Math.abs(word.score) / strongest;
            const pole = word.score >= 0 ? "var(--div-pos)" : "var(--div-neg)";
            return (
              <span
                key={`${word.text}-${index}`}
                className={strength > STRONG ? "lens-word lens-word-strong" : "lens-word"}
                style={{ background: `color-mix(in oklab, ${pole} ${Math.round(strength * 100)}%, var(--div-mid))` }}
                title={`${word.score >= 0 ? "toward" : "away"}: ${word.score.toFixed(4)}`}
              >
                {word.text}
              </span>
            );
          })}
        </p>
        <details>
          <summary>Show as a table</summary>
          <div className="lens-table-wrap">
            <table className="lens-table">
              <thead>
                <tr>
                  <th>Word</th>
                  <th className="num">Pull</th>
                </tr>
              </thead>
              <tbody>
                {attribution.respondent_words.map((word, index) => (
                  <tr key={`${word.text}-${index}`}>
                    <td>{word.text}</td>
                    <td className="num">{word.score.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>

      <section className="lens-section">
        <h2 className="lens-heading">Strongest tokens anywhere in the prompt</h2>
        <div className="lens-table-wrap">
          <table className="lens-table">
            <thead>
              <tr>
                <th>Token</th>
                <th>Part of the prompt</th>
                <th className="num">Pull</th>
              </tr>
            </thead>
            <tbody>
              {attribution.tokens.map((token) => (
                <tr key={token.position}>
                  <td>{visible(token.text)}</td>
                  <td>{labels.get(token.section) ?? token.section}</td>
                  <td className="num">{token.weight.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function PartTable({ rows }: { rows: { part: string; toward: number; away: number }[] }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th>Part of the prompt</th>
          <th className="num">Toward the pick</th>
          <th className="num">Away from it</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.part}>
            <td>{row.part}</td>
            <td className="num">{probability(row.toward)}</td>
            <td className="num">{probability(-row.away)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
