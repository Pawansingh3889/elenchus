"use client";

import { useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Gate } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { probability } from "@/lib/interpFormat";
import { dollars, milliseconds } from "@/lib/lensFormat";
import { useEvalItems, useFaithfulness, useJudgeRun, useLabel, useMe } from "@/lib/queries";
import type { EvalItem, FaithfulnessSlice, LabelVerdict, Rate } from "@/lib/schemas";

const PAGE = 10;
const VERDICTS: { verdict: LabelVerdict; label: string }[] = [
  { verdict: "supported", label: "Supported" },
  { verdict: "invented", label: "Invented" },
  { verdict: "unsure", label: "Unsure" },
];

/** A rate with its interval, or why there is none, and a warning below the minimum. */
function rate(value: Rate): string {
  if (value.value === null) return "none yet";
  const interval =
    value.low === null || value.high === null
      ? ""
      : ` (${probability(value.low)} to ${probability(value.high)})`;
  return `${probability(value.value)}${interval}${value.too_few ? ", too few" : ""}`;
}

/**
 * Evaluation: was each recorded answer what the respondent said. A person's label is the
 * truth; the judge model's verdict is shown beside it and scored against it, never used in
 * its place.
 */
export default function EvaluationPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const report = useFaithfulness(admin);

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Evaluation</h1>
        </div>
        <p className="lens-provenance">
          Faithfulness first: a person labels each recorded answer supported, invented or
          unsure, from what the respondent actually typed. Rates count only answers labelled
          supported or invented, carry a 95% Wilson interval, and are marked too few below
          twenty. The judge is a model; it is scored against the labels and never stands in for
          them.
        </p>
        <ErrorBanner error={report.error} />
        {report.data ? <Report overall={report.data.overall} slices={report.data} /> : null}
        <Queue admin={admin} />
      </div>
    </Gate>
  );
}

function Report({
  overall,
  slices,
}: {
  overall: FaithfulnessSlice;
  slices: { by_source: FaithfulnessSlice[]; by_answer_type: FaithfulnessSlice[]; by_model: FaithfulnessSlice[] };
}) {
  return (
    <>
      <div className="lens-tiles">
        <Tile label="Answers to evaluate" value={String(overall.items)} />
        <Tile
          label="Labelled"
          value={`${overall.labelled} (${overall.supported} supported, ${overall.invented} invented, ${overall.unsure} unsure)`}
        />
        <Tile label="Invention rate" value={rate(overall.invention_rate)} />
        <Tile label="Judge precision" value={rate(overall.judge_precision)} />
        <Tile label="Judge recall" value={rate(overall.judge_recall)} />
        <Tile label="Judge false alarms" value={rate(overall.judge_false_alarms)} />
      </div>
      <SliceTable title="By source" slices={slices.by_source} />
      <SliceTable title="By answer type" slices={slices.by_answer_type} />
      <SliceTable title="By model" slices={slices.by_model} />
    </>
  );
}

function SliceTable({ title, slices }: { title: string; slices: FaithfulnessSlice[] }) {
  return (
    <section className="lens-section">
      <h2 className="lens-heading">{title}</h2>
      <div className="lens-table-wrap">
        <table className="lens-table">
          <thead>
            <tr>
              <th />
              <th className="num">Answers</th>
              <th className="num">Labelled</th>
              <th className="num">Invented</th>
              <th>Invention rate</th>
              <th>Judge precision</th>
              <th>Judge recall</th>
              <th>Judge false alarms</th>
            </tr>
          </thead>
          <tbody>
            {slices.map((slice) => (
              <tr key={slice.name}>
                <td>{slice.name}</td>
                <td className="num">{slice.items}</td>
                <td className="num">{slice.labelled}</td>
                <td className="num">{slice.invented}</td>
                <td>{rate(slice.invention_rate)}</td>
                <td>{rate(slice.judge_precision)}</td>
                <td>{rate(slice.judge_recall)}</td>
                <td>{rate(slice.judge_false_alarms)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Queue({ admin }: { admin: boolean }) {
  const [source, setSource] = useState<"corpus" | "runs">("corpus");
  const [unlabelled, setUnlabelled] = useState(true);
  const [shown, setShown] = useState(PAGE);
  const items = useEvalItems(source, unlabelled, admin);
  const rows = items.data ?? [];

  return (
    <section className="lens-section">
      <h2 className="lens-heading">Label answers</h2>
      <div className="lens-eval-actions">
        {(["corpus", "runs"] as const).map((option) => (
          <button
            key={option}
            type="button"
            className={source === option ? "btn btn-primary" : "btn btn-secondary"}
            aria-pressed={source === option}
            onClick={() => {
              setSource(option);
              setShown(PAGE);
            }}
          >
            {option === "corpus" ? "Committed corpus" : "Runs in this database"}
          </button>
        ))}
        <label className="lens-toggle">
          <input type="checkbox" checked={unlabelled} onChange={(event) => setUnlabelled(event.target.checked)} />
          Only answers nobody has labelled
        </label>
      </div>
      <ErrorBanner error={items.error} />
      <p className="lens-note">
        {rows.length} {unlabelled ? "unlabelled " : ""}answers in this source.
      </p>
      <div className="lens-eval-list">
        {rows.slice(0, shown).map((item) => (
          <Item key={`${item.key}-${item.label ?? "none"}`} item={item} />
        ))}
      </div>
      {rows.length > shown ? (
        <button type="button" className="btn btn-secondary" onClick={() => setShown(shown + PAGE)}>
          Show {Math.min(PAGE, rows.length - shown)} more
        </button>
      ) : null}
    </section>
  );
}

function Item({ item }: { item: EvalItem }) {
  const [note, setNote] = useState(item.note ?? "");
  const label = useLabel();
  const judge = useJudgeRun();
  const judged = item.judge_supported !== null;

  return (
    <article className="lens-eval-item">
      <div className="lens-eval-meta">
        {item.origin} · {item.model ?? "model not recorded"} · {item.answer_type} · {item.kind}
        {item.marked_invented ? " · marked invented in the file" : ""}
      </div>
      <div className="lens-eval-question">{item.question_text}</div>
      {item.options.length > 0 ? (
        <div className="lens-eval-meta">Options: {item.options.join(" · ")}</div>
      ) : null}
      <div className="lens-eval-meta">What the respondent had said by then</div>
      {item.said.length > 0 ? (
        <ol className="lens-eval-said">
          {item.said.map((message, index) => (
            <li key={`${index}-${message}`}>{message}</li>
          ))}
        </ol>
      ) : (
        <p className="lens-note">
          Nothing: no respondent message came before this answer, as in seeded sample data.
        </p>
      )}
      <div className="lens-eval-meta">What was recorded</div>
      <pre className="lens-eval-value">{JSON.stringify(item.value, null, 2)}</pre>
      <div className="lens-eval-meta">
        {judged
          ? `Judge (${item.judge_prompt}): ${item.judge_supported ? "supported" : "flagged as invented"}. ${item.judge_why ?? ""}`
          : "Not judged."}
      </div>
      <ErrorBanner error={label.error ?? judge.error} />
      <div className="lens-eval-actions">
        {VERDICTS.map(({ verdict, label: text }) => (
          <button
            key={verdict}
            type="button"
            className={item.label === verdict ? "btn btn-primary" : "btn btn-secondary"}
            aria-pressed={item.label === verdict}
            disabled={label.isPending}
            onClick={() => label.mutate({ key: item.key, verdict, note: note.trim() || null })}
          >
            {text}
          </button>
        ))}
        <input
          type="text"
          value={note}
          placeholder="Note, optional"
          aria-label="Note"
          maxLength={2000}
          onChange={(event) => setNote(event.target.value)}
        />
        {item.source === "runs" && !judged && item.run_id !== null ? (
          <button
            type="button"
            className="btn btn-quiet"
            disabled={judge.isPending}
            onClick={() => judge.mutate(item.run_id as string)}
          >
            {judge.isPending ? "Judging this run" : "Judge this run"}
          </button>
        ) : null}
      </div>
      {judge.data ? (
        <div className="lens-eval-meta">
          Judged {judge.data.answers} answers with {judge.data.model ?? "an unrecorded model"}:{" "}
          {judge.data.flagged} flagged, {dollars(judge.data.cost_usd, judge.data.unmetered_calls)},{" "}
          {milliseconds(judge.data.duration_ms)}.
        </div>
      ) : null}
    </article>
  );
}
