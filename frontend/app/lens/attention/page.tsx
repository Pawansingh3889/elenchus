"use client";

import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { ChosenReading, InterpAsks } from "@/components/lens/InterpAsks";
import { Tile } from "@/components/lens/LensStripView";
import { byGroup, GROUPS, groupsOf, probability, visible } from "@/lib/interpFormat";
import { dollars, milliseconds } from "@/lib/lensFormat";
import { useSelectedAsk } from "@/lib/lensScope";
import { useInterpAnalysis, useMe } from "@/lib/queries";
import type { StoredAnalysis } from "@/lib/schemas";

/**
 * Attention: at the moment Qwen3-0.6B is about to write a tool's name, where each layer
 * looks in the prompt, averaged over heads, as a share per part of the prompt.
 */
export default function AttentionPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [selected] = useSelectedAsk();
  const analysis = useInterpAnalysis(selected, admin);

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Attention</h1>
        </div>
        <p className="lens-provenance">
          Qwen3-0.6B reading the exact prompt a hosted call was sent, never the hosted
          model&rsquo;s internals. For every layer, the attention of the moment the tool&rsquo;s
          name is about to be written, averaged over heads and summed per part of the prompt.
          Attention shows where the model looks, not why it chooses: the Token relationships
          page measures what moved the choice.
        </p>
        <InterpAsks admin={admin} need="reading" />
        <ErrorBanner error={analysis.error} />
        <ChosenReading selected={selected} loading={analysis.isFetching} stored={analysis.data}>
          {(stored) => <Attention key={stored.span_id} stored={stored} />}
        </ChosenReading>
      </div>
    </Gate>
  );
}

function Attention({ stored }: { stored: StoredAnalysis }) {
  const [withoutTemplate, setWithoutTemplate] = useState(true);
  const reading = stored.analysis;
  const groups = groupsOf(reading.sections);
  const parts = GROUPS.filter((group) => !(withoutTemplate && group.key === "template"));
  const rows = reading.attention.map((layer) => {
    const shares = byGroup(layer.shares, groups);
    const whole = withoutTemplate ? 1 - shares.template : 1;
    const row: Record<string, number> = { layer: layer.layer };
    for (const part of parts) row[part.key] = whole > 0 ? shares[part.key] / whole : 0;
    return row;
  });
  const last = byGroup(reading.attention[reading.attention.length - 1].shares, groups);
  const tokens = byGroup(
    Object.fromEntries(reading.sections.map((section) => [section.key, section.tokens])),
    groups,
  );
  const labels = new Map(reading.sections.map((section) => [section.key, section.label]));

  return (
    <>
      <div className="lens-tiles">
        <Tile label="Last layer: chat template" value={probability(last.template)} />
        <Tile label="Last layer: system prompt" value={probability(last.system)} />
        <Tile label="Last layer: tool definitions" value={probability(last.tools)} />
        <Tile label="Last layer: last respondent message" value={probability(last.last)} />
        <Tile label="Tokens in the last message" value={String(tokens.last)} />
        <Tile label="Prompt tokens" value={String(reading.prompt_tokens)} />
        <Tile label="Reading took" value={milliseconds(stored.duration_ms)} />
        <Tile label="Reading cost" value={dollars(stored.cost_usd)} />
      </div>

      <label className="lens-toggle">
        <input
          type="checkbox"
          checked={withoutTemplate}
          onChange={(event) => setWithoutTemplate(event.target.checked)}
        />
        Leave out the chat template tokens, where attention rests when it has nowhere to go
      </label>

      <ChartCard
        title="Where the decision looks, layer by layer"
        sample={`${reading.attention.length} layers; ${withoutTemplate ? "shares of the attention outside the template" : "shares of all attention"}`}
        legend={parts.map((part) => ({ label: part.label, color: part.color }))}
        table={<ShareTable rows={rows} parts={parts} />}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }} barCategoryGap={1}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="layer" {...axis} />
            <YAxis domain={[0, 1]} {...axis} width={44} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} />
            <Tooltip
              cursor={{ fill: "var(--highlight-soft)" }}
              content={(props) => (
                <LensTooltip {...props} hideZero format={probability} labelFormat={(label) => `layer ${String(label)}`} />
              )}
            />
            {parts.map((part) => (
              <Bar key={part.key} isAnimationActive={false} dataKey={part.key} name={part.label} stackId="shares" fill={part.color} stroke="var(--raised)" strokeWidth={1} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <section className="lens-section">
        <h2 className="lens-heading">Most attended tokens</h2>
        <p className="lens-note">
          Averaged over every layer, leaving out the chat template tokens.
        </p>
        <div className="lens-table-wrap">
          <table className="lens-table">
            <thead>
              <tr>
                <th>Token</th>
                <th>Part of the prompt</th>
                <th className="num">Share of attention</th>
              </tr>
            </thead>
            <tbody>
              {reading.attended_tokens.map((token) => (
                <tr key={token.position}>
                  <td>{visible(token.text)}</td>
                  <td>{labels.get(token.section) ?? token.section}</td>
                  <td className="num">{probability(token.weight)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function ShareTable({ rows, parts }: { rows: Record<string, number>[]; parts: { key: string; label: string }[] }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th className="num">Layer</th>
          {parts.map((part) => (
            <th key={part.key} className="num">
              {part.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.layer}>
            <td className="num">{row.layer}</td>
            {parts.map((part) => (
              <td key={part.key} className="num">
                {probability(row[part.key])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
