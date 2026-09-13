"use client";

import { useMemo, useState } from "react";

import { dollars, milliseconds, moment, tokenCount } from "@/lib/lensFormat";
import type { Span } from "@/lib/schemas";

type Row = { span: Span; depth: number; turn: Span };

/** Depth-first, oldest first, each node carrying the turn it belongs to. */
function rowsOf(spans: Span[]): Row[] {
  const children = new Map<string | null, Span[]>();
  for (const span of spans) {
    const siblings = children.get(span.parent_id);
    if (siblings) siblings.push(span);
    else children.set(span.parent_id, [span]);
  }
  const rows: Row[] = [];
  const walk = (parent: string | null, depth: number, turn: Span | null) => {
    const siblings = children.get(parent);
    if (!siblings) return;
    siblings.sort((a, b) => Date.parse(a.started_at) - Date.parse(b.started_at));
    for (const span of siblings) {
      const owner = turn ?? span;
      rows.push({ span, depth, turn: owner });
      walk(span.id, depth + 1, owner);
    }
  };
  walk(null, 0, null);
  return rows;
}

function describe(span: Span): string {
  const attr = (key: string) => (span.attrs[key] === undefined ? "" : String(span.attrs[key]));
  switch (span.kind) {
    case "turn":
      return `turn, question ${Number(span.attrs.question_index ?? 0) + 1}`;
    case "decision":
      return `${attr("retry") === "true" ? "retry" : "ask"} → ${attr("resolved_to") || "failed"}`;
    case "validation":
      return `${attr("tool")} ${attr("outcome")}`;
    case "attempt":
      return `tier ${span.tier ?? "?"} ${span.model ?? ""} · ${span.status ?? "no status"}`;
  }
}

function failed(span: Span): boolean {
  return span.error !== null || span.attrs.outcome === "refused";
}

/**
 * One run's trace as a waterfall.
 *
 * Each bar is placed and sized against the turn it belongs to, so a turn reads left to
 * right as the respondent's wait: which asks it made, which tiers were tried, and how long
 * each took. On an attempt the lighter part of the bar is the time before the first token,
 * the rest is writing. Nothing here is estimated: every figure is a span's own record.
 */
export function SpanTree({ spans }: { spans: Span[] }) {
  const rows = useMemo(() => rowsOf(spans), [spans]);
  const [selectedId, setSelectedId] = useState<string | null>(rows[0]?.span.id ?? null);
  const selected = rows.find((row) => row.span.id === selectedId)?.span ?? null;

  return (
    <div className="lens-split">
      <ol className="lens-tree" aria-label="Spans, oldest first">
        {rows.map(({ span, depth, turn }) => {
          const window = Math.max(turn.duration_ms, 1);
          const offset = Math.min(
            100,
            Math.max(0, ((Date.parse(span.started_at) - Date.parse(turn.started_at)) / window) * 100),
          );
          const width = Math.min(100 - offset, (span.duration_ms / window) * 100);
          const wait =
            span.first_token_ms === null ? 0 : Math.min(width, (span.first_token_ms / window) * 100);
          return (
            <li key={span.id}>
              <button
                type="button"
                className={failed(span) ? "lens-node lens-node-failed" : "lens-node"}
                aria-pressed={span.id === selectedId}
                onClick={() => setSelectedId(span.id)}
              >
                <span className="lens-node-label" style={{ paddingInlineStart: `${depth * 16}px` }}>
                  <span className={`lens-kind lens-kind-${span.kind}`}>{span.kind}</span>
                  <span className="lens-node-name">{describe(span)}</span>
                </span>
                <span className="lens-track" aria-hidden>
                  <span
                    className="lens-bar"
                    style={{ insetInlineStart: `${offset}%`, inlineSize: `${width}%` }}
                  />
                  {wait > 0 ? (
                    <span
                      className="lens-bar-wait"
                      style={{ insetInlineStart: `${offset}%`, inlineSize: `${wait}%` }}
                    />
                  ) : null}
                </span>
                <span className="lens-node-ms">{milliseconds(span.duration_ms)}</span>
              </button>
            </li>
          );
        })}
      </ol>
      {selected ? <SpanDetail span={selected} /> : null}
    </div>
  );
}

function SpanDetail({ span }: { span: Span }) {
  const writing =
    span.first_token_ms === null ? null : Math.max(0, span.duration_ms - span.first_token_ms);
  const facts: [string, string][] = [
    ["Kind", `${span.kind} (${span.name})`],
    ["Started", moment(span.started_at)],
    ["Took", milliseconds(span.duration_ms)],
  ];
  if (span.kind === "attempt") {
    facts.push(
      ["Before first token", milliseconds(span.first_token_ms)],
      ["Writing", milliseconds(writing)],
      ["Tier", span.tier === null ? "not reported" : String(span.tier)],
      ["Model", span.model ?? "not reported"],
      ["Status", span.status === null ? "not reported" : String(span.status)],
      ["Tokens in", tokenCount(span.prompt_tokens)],
      ["of which cached", tokenCount(span.cached_tokens)],
      ["Tokens out", tokenCount(span.completion_tokens)],
      ["of which reasoning", tokenCount(span.reasoning_tokens)],
      ["Cost", dollars(span.cost_usd)],
    );
  }
  if (span.prompt_version) facts.push(["Prompt", span.prompt_version]);
  if (span.error) facts.push(["Error", span.error]);

  return (
    <aside className="card lens-detail" aria-live="polite">
      <div className="card-label">Selected span</div>
      <dl>
        {facts.map(([label, value]) => (
          <div key={label} className="lens-fact">
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {Object.keys(span.attrs).length > 0 ? (
        <>
          <div className="card-label">What the engine knew</div>
          <pre>{JSON.stringify(span.attrs, null, 2)}</pre>
        </>
      ) : null}
    </aside>
  );
}
