"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { SignInPrompt } from "@/components/SignInPrompt";
import { Stat } from "@/components/Stat";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useLlmRunEntries, useMe } from "@/lib/queries";
import { useUserStore } from "@/lib/store";
import type { LlmEntry } from "@/lib/types";

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
  return `$${usd.toFixed(4)}`;
}

type SortDir = "asc" | "desc";

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="ml-1 text-muted/50">&#8597;</span>;
  return <span className="ml-1">{dir === "asc" ? "&#9650;" : "&#9660;"}</span>;
}

function entrySortKey(field: string, e: LlmEntry): number | string {
  switch (field) {
    case "time": return e.ts;
    case "op": return e.op ?? "";
    case "model": return e.model ?? "";
    case "prompt": return e.prompt_tokens ?? 0;
    case "completion": return e.completion_tokens ?? 0;
    case "latency": return e.latency_ms ?? 0;
    case "cost": return e.cost_usd ?? 0;
    case "status": return e.status ?? "";
    default: return "";
  }
}

export default function AdminRunDetailPage() {
  const { id: runId } = useParams<{ id: string }>();
  const currentUserId = useUserStore((s) => s.currentUserId);
  const { data: me } = useMe();
  const { data: entries, isLoading, error } = useLlmRunEntries(runId);
  const router = useRouter();
  const [sort, setSort] = useState<{ field: string; dir: SortDir }>({ field: "time", dir: "asc" });

  const isAdmin = me?.is_admin ?? false;
  useEffect(() => {
    if (me && !isAdmin) router.replace("/dashboard");
  }, [me, isAdmin, router]);

  function toggleSort(field: string) {
    setSort((prev) => ({
      field,
      dir: prev.field === field && prev.dir === "asc" ? "desc" : "asc",
    }));
  }

  const sorted = useMemo(() => {
    if (!entries) return [];
    const list = [...entries];
    list.sort((a, b) => {
      const av = entrySortKey(sort.field, a);
      const bv = entrySortKey(sort.field, b);
      if (typeof av === "string" && typeof bv === "string") {
        return sort.dir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sort.dir === "asc" ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });
    return list;
  }, [entries, sort]);

  if (!currentUserId) return <SignInPrompt />;
  if (!isAdmin) return <p className="p-6 text-muted">This page requires an administrator account.</p>;

  const totalPrompt = entries?.reduce((s, e) => s + (e.prompt_tokens ?? 0), 0) ?? 0;
  const totalCompletion = entries?.reduce((s, e) => s + (e.completion_tokens ?? 0), 0) ?? 0;
  const totalCost = entries?.reduce((s, e) => s + (e.cost_usd ?? 0), 0) ?? 0;
  const totalLatency = entries?.reduce((s, e) => s + (e.latency_ms ?? 0), 0) ?? 0;
  const errorCount = entries?.filter((e) => e.error).length ?? 0;
  const avgLatency = entries?.length ? totalLatency / entries.length : 0;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 p-4">
      {error ? <ErrorBanner error={error} /> : null}

      <div className="flex items-center gap-3">
        <a href="/admin" className="text-sm text-ink underline-offset-2 hover:underline">&larr; Back</a>
        <h1 className="text-md font-semibold">Run {runId.slice(0, 12)}...</h1>
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-60 w-full" />
        </div>
      ) : null}

      {entries ? (
        <>
          <Card className="flex flex-col gap-3 p-4">
            <div className="flex flex-wrap gap-6">
              <Stat value={entries.length} label="Calls" />
              <Stat value={formatTokens(totalPrompt)} label="Prompt tokens" />
              <Stat value={formatTokens(totalCompletion)} label="Completion tokens" />
              <Stat value={formatMs(avgLatency)} label="Avg latency" />
              <Stat value={formatCost(totalCost)} label="Total cost" />
              <Stat
                value={errorCount}
                label="Errors"
                className={errorCount > 0 ? "text-warn-text" : undefined}
              />
            </div>
          </Card>

          <Card className="overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
                  <th className="px-3 py-2">#</th>
                  <th className="px-3 py-2 cursor-pointer select-none" onClick={() => toggleSort("time")}>
                    Time<SortIcon active={sort.field === "time"} dir={sort.dir} />
                  </th>
                  <th className="px-3 py-2 cursor-pointer select-none" onClick={() => toggleSort("op")}>
                    Op<SortIcon active={sort.field === "op"} dir={sort.dir} />
                  </th>
                  <th className="px-3 py-2 cursor-pointer select-none" onClick={() => toggleSort("model")}>
                    Model<SortIcon active={sort.field === "model"} dir={sort.dir} />
                  </th>
                  <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleSort("prompt")}>
                    Prompt<SortIcon active={sort.field === "prompt"} dir={sort.dir} />
                  </th>
                  <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleSort("completion")}>
                    Completion<SortIcon active={sort.field === "completion"} dir={sort.dir} />
                  </th>
                  <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleSort("latency")}>
                    Latency<SortIcon active={sort.field === "latency"} dir={sort.dir} />
                  </th>
                  <th className="px-3 py-2 text-right cursor-pointer select-none" onClick={() => toggleSort("cost")}>
                    Cost<SortIcon active={sort.field === "cost"} dir={sort.dir} />
                  </th>
                  <th className="px-3 py-2 cursor-pointer select-none" onClick={() => toggleSort("status")}>
                    Status<SortIcon active={sort.field === "status"} dir={sort.dir} />
                  </th>
                  <th className="px-3 py-2">Error</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((e, i) => (
                  <tr
                    key={`${e.ts}-${i}`}
                    className="border-b border-border last:border-0"
                  >
                    <td className="px-3 py-2 tabular-nums text-muted">{i + 1}</td>
                    <td className="px-3 py-2 tabular-nums text-xs">
                      {e.ts ? new Date(e.ts).toLocaleString() : "-"}
                    </td>
                    <td className="px-3 py-2">{e.op ?? "-"}</td>
                    <td className="px-3 py-2 font-medium">{e.model ?? "-"}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {e.prompt_tokens != null ? formatTokens(e.prompt_tokens) : "-"}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {e.completion_tokens != null ? formatTokens(e.completion_tokens) : "-"}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {e.latency_ms != null ? formatMs(e.latency_ms) : "-"}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {e.cost_usd != null ? formatCost(e.cost_usd) : "-"}
                    </td>
                    <td className="px-3 py-2">
                      {e.error ? (
                        <span className="text-warn-text">error</span>
                      ) : (
                        <span className="text-muted">{e.status ?? "-"}</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs text-warn-text max-w-[200px] truncate" title={e.error ?? undefined}>
                      {e.error ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      ) : null}
    </div>
  );
}
