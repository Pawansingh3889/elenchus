"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { SignInPrompt } from "@/components/SignInPrompt";
import { Stat } from "@/components/Stat";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useLlmReport, useLlmRunEntries, useMe, useAdminHealth } from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import type { LlmEntry, LlmModelStats, LlmRunSummary } from "@/lib/types";

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function formatMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

function formatCost(usd: number): string {
  if (usd === 0) return "$0.00";
  if (usd < 0.01) return "<$0.01";
  return `$${usd.toFixed(2)}`;
}

function tsShort(ts: string): string {
  if (!ts) return "-";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

type SortDir = "asc" | "desc";

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  return (
    <span className={`ml-1 ${active ? "text-ink" : "text-muted"}`}>
      {dir === "asc" ? "\u25B2" : "\u25BC"}
    </span>
  );
}

function modelSortKey(field: string, m: LlmModelStats): number {
  switch (field) {
    case "model":
      return m.model.localeCompare("");
    case "tier":
      return m.tier ?? 0;
    case "calls":
      return m.calls;
    case "prompt_tokens":
      return m.total_prompt_tokens;
    case "context_tokens":
      return m.total_context_tokens;
    case "latency":
      return m.avg_latency_ms;
    case "errors":
      return m.error_count;
    default:
      return 0;
  }
}

function runSortKey(field: string, r: LlmRunSummary): number | string {
  switch (field) {
    case "run":
      return r.run_id ?? "";
    case "model":
      return r.model;
    case "calls":
      return r.calls;
    case "prompt_tokens":
      return r.prompt_tokens;
    case "context_tokens":
      return r.context_tokens;
    case "latency":
      return r.avg_latency_ms;
    case "errors":
      return r.error_count;
    case "time":
      return r.last_ts;
    default:
      return 0;
  }
}

function EntryRow({ e }: { e: LlmEntry }) {
  return (
    <tr className="border-b border-border last:border-0">
      <td className="px-3 py-2 text-xs text-muted whitespace-nowrap">{tsShort(e.ts)}</td>
      <td className="px-3 py-2 text-xs">{e.op ?? "-"}</td>
      <td className="px-3 py-2 text-right tabular-nums">{e.tier ?? "-"}</td>
      <td className="px-3 py-2 text-xs">{e.model ?? "-"}</td>
      <td className="px-3 py-2 text-right tabular-nums">{formatTokens(e.prompt_tokens ?? 0)}</td>
      <td className="px-3 py-2 text-right tabular-nums">{formatTokens(e.context_tokens ?? (e.prompt_tokens ?? 0) + (e.completion_tokens ?? 0))}</td>
      <td className="px-3 py-2 text-right tabular-nums">{formatMs(e.latency_ms ?? 0)}</td>
      <td className="px-3 py-2 text-right tabular-nums">
        {e.status ? <span className={e.status >= 400 ? "text-warn-text" : ""}>{e.status}</span> : "-"}
      </td>
      <td className="px-3 py-2 text-xs">
        {e.error ? <span className="text-warn-text">{e.error}</span> : "-"}
      </td>
      <td className="px-3 py-2 text-right tabular-nums">{formatCost(e.cost_usd ?? 0)}</td>
    </tr>
  );
}

function ExpandedEntries({ runId }: { runId: string }) {
  const { data: entries, isLoading, error } = useLlmRunEntries(runId);
  if (isLoading) return <tr><td colSpan={10} className="px-3 py-2"><Skeleton className="h-16 w-full" /></td></tr>;
  if (error) return <tr><td colSpan={10} className="px-3 py-2 text-sm text-warn-text">Failed to load entries</td></tr>;
  if (!entries || entries.length === 0) return <tr><td colSpan={10} className="px-3 py-2 text-sm text-muted">No entries for this run.</td></tr>;
  return (
    <>
      {entries.map((e) => (
        <EntryRow key={e.ts + e.op} e={e} />
      ))}
    </>
  );
}

function HealthCheckCard() {
  const { data: health, isLoading, error } = useAdminHealth();
  if (isLoading) return <Card className="p-4"><Skeleton className="h-16 w-full" /></Card>;
  if (error) return <Card className="p-4 text-sm text-warn-text">Failed to load health</Card>;
  if (!health) return null;

  return (
    <Card className="flex flex-col gap-3 p-4">
      <h2 className="text-md font-semibold">System Health</h2>
      <div className="flex flex-wrap gap-6">
        <Stat value={health.status === "ok" ? "Healthy" : "Degraded"} label="Status" />
        <Stat value={health.database === "ok" ? "Database OK" : "Database unreachable"} label="Database" />
        <Stat value={health.demo_mode ? "Demo" : "Production"} label="Environment" />
      </div>
    </Card>
  );
}

export default function AdminPage() {
  const currentUserId = useUserStore((s) => s.currentUserId);
  const { data: me } = useMe();
  const { data: report, isLoading, error } = useLlmReport();
  const router = useRouter();
  const [expandedRun, setExpandedRun] = useState<string | null>(null);

  const [modelSort, setModelSort] = useState<{ field: string; dir: SortDir }>({ field: "calls", dir: "desc" });
  const [runSort, setRunSort] = useState<{ field: string; dir: SortDir }>({ field: "time", dir: "desc" });
  const [errorFilter, setErrorFilter] = useState<"all" | "errors" | "clean">("all");
  const [opFilter, setOpFilter] = useState<string>("all");

  const isAdmin = me?.is_admin ?? false;
  useEffect(() => {
    if (me && !isAdmin) router.replace("/dashboard");
  }, [me, isAdmin, router]);

  const sortedModels = useMemo(() => {
    if (!report) return [];
    const list = [...report.models];
    list.sort((a, b) => {
      const av = modelSortKey(modelSort.field, a);
      const bv = modelSortKey(modelSort.field, b);
      return modelSort.dir === "asc" ? av - bv : bv - av;
    });
    return list;
  }, [report, modelSort]);

  const uniqueOps = useMemo(() => {
    if (!report) return [];
    const ops = new Set<string>();
    for (const r of report.runs) {
      for (const op of r.ops) ops.add(op);
    }
    return [...ops].sort();
  }, [report]);

  const sortedRuns = useMemo(() => {
    if (!report) return [];
    let list = [...report.runs];

    if (errorFilter === "errors") list = list.filter((r) => r.error_count > 0);
    else if (errorFilter === "clean") list = list.filter((r) => r.error_count === 0);

    if (opFilter !== "all") list = list.filter((r) => r.ops.includes(opFilter));

    list.sort((a, b) => {
      const aNoRun = !(a.run_id);
      const bNoRun = !(b.run_id);
      if (aNoRun && !bNoRun) return 1;
      if (!aNoRun && bNoRun) return -1;
      const av = runSortKey(runSort.field, a);
      const bv = runSortKey(runSort.field, b);
      if (typeof av === "string" && typeof bv === "string") return av.localeCompare(bv);
      if (typeof av === "number" && typeof bv === "number") return av - bv;
      return 0;
    });
    return list;
  }, [report, errorFilter, opFilter, runSort]);

  function toggleModelSort(field: string) {
    setModelSort((prev) => ({
      field,
      dir: prev.field === field && prev.dir === "desc" ? "asc" : "desc",
    }));
  }

  function toggleRunSort(field: string) {
    setRunSort((prev) => ({
      field,
      dir: prev.field === field && prev.dir === "desc" ? "asc" : "desc",
    }));
  }

  if (!currentUserId) return <SignInPrompt />;
  if (me && !isAdmin) return <SignInPrompt />;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-ink">Admin</h1>
        <p className="text-sm text-muted">LLM usage, spend, and system health.</p>
      </div>

      {error ? (
        <ErrorBanner error={error instanceof Error ? error : "Failed to load report"} />
      ) : null}

      <HealthCheckCard />

      {isLoading ? (
        <Card className="p-4"><Skeleton className="h-16 w-full" /></Card>
      ) : report ? (
        <>
          <section className="flex flex-col gap-2">
            <div className="flex items-center gap-3">
              <h2 className="text-md font-semibold">By Model</h2>
              <div className="flex gap-4 text-xs text-muted">
                <span>Calls: {report.total_entries}</span>
                <span>Runs: {report.total_runs}</span>
                <span>Prompt: {formatTokens(report.total_prompt_tokens)}</span>
                <span>Context: {formatTokens(report.total_context_tokens)}</span>
                <span>Cost: {formatCost(report.total_cost_usd)}</span>
                <span>Avg latency: {formatMs(report.avg_latency_ms)}</span>
              </div>
            </div>
            <Card className="overflow-x-auto p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
                    <th className="px-3 py-2 cursor-pointer select-none" onClick={() => toggleModelSort("model")}>
                      Model<SortIcon active={modelSort.field === "model"} dir={modelSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleModelSort("tier")}>
                      Tier<SortIcon active={modelSort.field === "tier"} dir={modelSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleModelSort("calls")}>
                      Calls<SortIcon active={modelSort.field === "calls"} dir={modelSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleModelSort("prompt_tokens")}>
                      Prompt tokens<SortIcon active={modelSort.field === "prompt_tokens"} dir={modelSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleModelSort("context_tokens")}>
                      Context tokens<SortIcon active={modelSort.field === "context_tokens"} dir={modelSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleModelSort("latency")}>
                      Avg latency<SortIcon active={modelSort.field === "latency"} dir={modelSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleModelSort("errors")}>
                      Errors<SortIcon active={modelSort.field === "errors"} dir={modelSort.dir} />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedModels.map((m) => (
                    <tr key={`${m.model}-${m.tier}`} className="border-b border-border last:border-0">
                      <td className="px-3 py-2 font-medium">{m.model}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{m.tier ?? "-"}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{m.calls}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{formatTokens(m.total_prompt_tokens)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{formatTokens(m.total_context_tokens)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{formatMs(m.avg_latency_ms)}</td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {m.error_count > 0 ? <span className="text-warn-text">{m.error_count}</span> : "0"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </section>

          <section className="flex flex-col gap-2">
            <div className="flex items-center gap-3">
              <h2 className="text-md font-semibold">Runs</h2>
              <select
                className="field w-auto text-xs"
                value={errorFilter}
                onChange={(e) => setErrorFilter(e.target.value as "all" | "errors" | "clean")}
              >
                <option value="all">All statuses</option>
                <option value="errors">Has errors</option>
                <option value="clean">No errors</option>
              </select>
              {uniqueOps.length > 1 ? (
                <select
                  className="field w-auto text-xs"
                  value={opFilter}
                  onChange={(e) => setOpFilter(e.target.value)}
                >
                  <option value="all">All ops</option>
                  {uniqueOps.map((op) => (
                    <option key={op} value={op}>{op}</option>
                  ))}
                </select>
              ) : null}
              {(errorFilter !== "all" || opFilter !== "all") ? (
                <button
                  className="text-xs text-muted hover:text-ink"
                  onClick={() => { setErrorFilter("all"); setOpFilter("all"); }}
                >
                  Clear filters
                </button>
              ) : null}
              {errorFilter !== "all" || opFilter !== "all" ? (
                <span className="text-xs text-muted">{sortedRuns.length} of {report.runs.length} runs</span>
              ) : null}
            </div>
            <Card className="overflow-x-auto p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
                    <th className="px-3 py-2" />
                    <th className="px-3 py-2 cursor-pointer select-none" onClick={() => toggleRunSort("run")}>
                      Run<SortIcon active={runSort.field === "run"} dir={runSort.dir} />
                    </th>
                    <th className="px-3 py-2 cursor-pointer select-none" onClick={() => toggleRunSort("model")}>
                      Model<SortIcon active={runSort.field === "model"} dir={runSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleRunSort("calls")}>
                      Calls<SortIcon active={runSort.field === "calls"} dir={runSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleRunSort("prompt_tokens")}>
                      Prompt<SortIcon active={runSort.field === "prompt_tokens"} dir={runSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleRunSort("context_tokens")}>
                      Context<SortIcon active={runSort.field === "context_tokens"} dir={runSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleRunSort("latency")}>
                      Avg latency<SortIcon active={runSort.field === "latency"} dir={runSort.dir} />
                    </th>
                    <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleRunSort("errors")}>
                      Errors<SortIcon active={runSort.field === "errors"} dir={runSort.dir} />
                    </th>
                    <th className="px-3 py-2 cursor-pointer select-none" onClick={() => toggleRunSort("time")}>
                      Time<SortIcon active={runSort.field === "time"} dir={runSort.dir} />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedRuns.map((r) => {
                    const id = r.run_id ?? "";
                    const isOpen = expandedRun === id;
                    return (
                      <>
                        <tr
                          key={id || r.first_ts}
                          className="cursor-pointer border-b border-border last:border-0 hover:bg-muted/50"
                          onClick={() => setExpandedRun(isOpen ? null : id || null)}
                        >
                          <td className="px-3 py-2 text-muted">{isOpen ? "\u25BC" : "\u25B6"}</td>
                          <td className="px-3 py-2 font-mono text-xs">{id ? id.slice(0, 12) : "no run"}</td>
                          <td className="px-3 py-2">{r.model}</td>
                          <td className="px-3 py-2 text-right tabular-nums">{r.calls}</td>
                          <td className="px-3 py-2 text-right tabular-nums">{formatTokens(r.prompt_tokens)}</td>
                          <td className="px-3 py-2 text-right tabular-nums">{formatTokens(r.context_tokens)}</td>
                          <td className="px-3 py-2 text-right tabular-nums">{formatMs(r.avg_latency_ms)}</td>
                          <td className="px-3 py-2 text-right tabular-nums">
                            {r.error_count > 0 ? <span className="text-warn-text">{r.error_count}</span> : "0"}
                          </td>
                          <td className="px-3 py-2 text-xs text-muted">
                            {r.first_ts ? (
                              r.first_ts !== r.last_ts
                                ? `${new Date(r.first_ts).toLocaleDateString()} \u2013 ${new Date(r.last_ts).toLocaleDateString()}`
                                : new Date(r.first_ts).toLocaleString()
                            ) : "-"}
                          </td>
                        </tr>
                        {isOpen && id ? <ExpandedEntries key={`exp-${id}`} runId={id} /> : null}
                      </>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          </section>
        </>
      ) : null}
    </div>
  );
}
