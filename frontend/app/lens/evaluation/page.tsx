"use client";

import { useState } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorBanner } from "@/components/ErrorBanner";
import { axis, ChartCard, Gate, LensTooltip } from "@/components/lens/Chart";
import { Tile } from "@/components/lens/LensStripView";
import { probability } from "@/lib/interpFormat";
import { dollars, median, milliseconds, moment, TOO_FEW } from "@/lib/lensFormat";
import {
  useComparison,
  useEvalItems,
  useEvalOptions,
  useEvalRuns,
  useStartEval,
  useFaithfulness,
  useJudgeRun,
  useLabel,
  useMe,
  useQuality,
} from "@/lib/queries";
import type {
  Agreement,
  ComparisonGroup,
  ComparisonReport,
  EvalOptions,
  EvalRun,
  EvalItem,
  FaithfulnessSlice,
  LabelVerdict,
  Median,
  QualitySlice,
  Rate,
} from "@/lib/schemas";

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

/** A median with how many measurements it covers, or why there is none. */
function middle(value: Median, format: (value: number) => string): string {
  return value.value === null ? "none" : `${format(value.value)} (n ${value.n})`;
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
  const quality = useQuality(admin);
  const comparison = useComparison(admin);

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
        <ErrorBanner error={quality.error} />
        {quality.data ? (
          <Quality
            overall={quality.data.overall}
            skipped={quality.data.runs_without_conversation}
            groups={quality.data}
          />
        ) : null}
        <ErrorBanner error={comparison.error} />
        {comparison.data ? <Comparison report={comparison.data} /> : null}
        <Runs admin={admin} />
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

function Quality({
  overall,
  skipped,
  groups,
}: {
  overall: QualitySlice;
  skipped: number;
  groups: { by_survey: QualitySlice[]; by_model: QualitySlice[]; by_prompt: QualitySlice[] };
}) {
  return (
    <section className="lens-section">
      <h2 className="lens-heading">How the conversations went</h2>
      <p className="lens-note">
        Measured from what runs record, with no model asked for an opinion. {skipped} runs have
        no respondent message, such as seeded sample data, and are counted here but not
        measured.
      </p>
      <div className="lens-tiles">
        <Tile label="Conversations" value={String(overall.runs)} />
        <Tile label="Completed" value={rate(overall.completion)} />
        <Tile label="Answers that record a refusal" value={rate(overall.declined)} />
        <Tile label="Messages per recorded answer" value={middle(overall.turns_per_answer, (v) => v.toFixed(2))} />
        <Tile label="Wait for each reply" value={middle(overall.wait_ms_per_turn, milliseconds)} />
        <Tile label="Cost per completed run" value={middle(overall.cost_per_completed_run, (v) => dollars(v, overall.unmetered_calls))} />
        <Tile label="Follow-ups asked, recorded" value={`${overall.follow_ups_asked}, ${overall.follow_up_answers}`} />
        <Tile label="New words a follow-up drew" value={middle(overall.follow_up_new_words, probability)} />
      </div>
      <QualityTable title="By survey" slices={groups.by_survey} />
      <QualityTable title="By model" slices={groups.by_model} />
      <QualityTable title="By prompt version" slices={groups.by_prompt} />
    </section>
  );
}

function QualityTable({ title, slices }: { title: string; slices: QualitySlice[] }) {
  return (
    <div className="lens-table-wrap">
      <table className="lens-table">
        <caption className="lens-note">{title}</caption>
        <thead>
          <tr>
            <th />
            <th className="num">Runs</th>
            <th>Completed</th>
            <th>Refusals recorded</th>
            <th>Messages per answer</th>
            <th>Characters typed</th>
            <th>Minutes to complete</th>
            <th>Wait per reply</th>
            <th>Follow-ups (asked, recorded, new words)</th>
            <th>Cost per completed run</th>
            <th className="num">Cost per answer</th>
          </tr>
        </thead>
        <tbody>
          {slices.map((slice) => (
            <tr key={slice.name}>
              <td>{slice.name}</td>
              <td className="num">{slice.runs}</td>
              <td>{rate(slice.completion)}</td>
              <td>{rate(slice.declined)}</td>
              <td>{middle(slice.turns_per_answer, (v) => v.toFixed(2))}</td>
              <td>{middle(slice.respondent_chars, (v) => String(Math.round(v)))}</td>
              <td>{middle(slice.minutes_to_complete, (v) => v.toFixed(1))}</td>
              <td>{middle(slice.wait_ms_per_turn, milliseconds)}</td>
              <td>
                {slice.follow_ups_asked}, {slice.follow_up_answers},{" "}
                {middle(slice.follow_up_new_words, probability)}
              </td>
              <td>{middle(slice.cost_per_completed_run, (v) => dollars(v, slice.unmetered_calls))}</td>
              <td className="num">
                {slice.cost_per_answer === null ? "none" : dollars(slice.cost_per_answer, slice.unmetered_calls)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Runs({ admin }: { admin: boolean }) {
  const options = useEvalOptions(admin);
  const runs = useEvalRuns(admin);
  return (
    <section className="lens-section">
      <h2 className="lens-heading">Evaluation runs</h2>
      <p className="lens-note">
        Scripted scenarios held through the real engine, pinned to one tier and one prompt
        version, under a spend cap for the whole batch. Each builds its own survey for an
        evaluation respondent who holds no job, so no reach count moves. A run stops at the
        turn that reaches the cap, and the rest of the batch does not start. Broad and evasive draft
        their survey from a brief first, and the draft is paid from the same cap.
      </p>
      <ErrorBanner error={options.error ?? runs.error} />
      {options.data ? <StartForm options={options.data} history={runs.data ?? []} /> : null}
      <RunTable runs={runs.data ?? []} />
    </section>
  );
}

function StartForm({ options, history }: { options: EvalOptions; history: EvalRun[] }) {
  const [chosen, setChosen] = useState<string[]>([]);
  const [tier, setTier] = useState<number | null>(options.tiers[0]?.tier ?? null);
  const [prompt, setPrompt] = useState(options.active_prompt);
  const [cap, setCap] = useState("1.00");
  const [confirming, setConfirming] = useState(false);
  const start = useStartEval();
  const capValue = Number(cap);
  const capOk = Number.isFinite(capValue) && capValue > 0 && capValue <= 25;

  // An estimate only from earlier runs pinned the same way, never a guess.
  const estimates = chosen.map((key) => {
    const earlier = history.filter(
      (run) =>
        run.scenario === key &&
        run.tier === tier &&
        run.prompt_version === prompt &&
        run.status === "completed",
    );
    return { key, cost: median(earlier.map((run) => run.cost_usd)), n: earlier.length };
  });
  const known = estimates.filter((e) => e.cost !== null);
  const estimate =
    chosen.length === 0
      ? "Choose at least one scenario."
      : known.length === 0
        ? "No earlier run pinned this way to estimate from."
        : `About ${dollars(known.reduce((sum, e) => sum + (e.cost ?? 0), 0))} for ${known.length} of ${chosen.length} scenarios, from earlier runs pinned this way.`;

  if (options.tiers.length === 0) {
    return <p className="lens-note">No tier is enabled on this deployment, so nothing can run.</p>;
  }
  return (
    <div className="lens-eval-item">
      <div className="lens-eval-meta">Scenarios</div>
      <div className="lens-eval-actions">
        {options.scenarios.map((scenario) => (
          <label key={scenario.key} className="lens-toggle" title={scenario.title}>
            <input
              type="checkbox"
              checked={chosen.includes(scenario.key)}
              onChange={(event) => {
                setConfirming(false);
                setChosen(
                  event.target.checked
                    ? [...chosen, scenario.key]
                    : chosen.filter((key) => key !== scenario.key),
                );
              }}
            />
            {scenario.key} (
            {scenario.generated
              ? `drafted, ${scenario.questions} questions asked for`
              : `${scenario.questions} questions`}
            )
          </label>
        ))}
      </div>
      <div className="lens-eval-actions">
        <label className="lens-filter">
          <span>Tier</span>
          <select
            value={tier ?? ""}
            onChange={(event) => {
              setConfirming(false);
              setTier(Number(event.target.value));
            }}
          >
            {options.tiers.map((option) => (
              <option key={option.tier} value={option.tier}>
                Tier {option.tier}, {option.model}
              </option>
            ))}
          </select>
        </label>
        <label className="lens-filter">
          <span>Prompt</span>
          <select
            value={prompt}
            onChange={(event) => {
              setConfirming(false);
              setPrompt(event.target.value);
            }}
          >
            {options.prompt_versions.map((name) => (
              <option key={name} value={name}>
                {name}
                {name === options.active_prompt ? " (active)" : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="lens-filter">
          <span>Cap, USD</span>
          <input
            type="number"
            min="0.000001"
            max="25"
            step="0.01"
            value={cap}
            onChange={(event) => {
              setConfirming(false);
              setCap(event.target.value);
            }}
          />
        </label>
      </div>
      <p className="lens-note">{estimate}</p>
      <ErrorBanner error={start.error} />
      <div className="lens-eval-actions">
        {confirming ? (
          <>
            <button
              type="button"
              className="btn btn-primary"
              disabled={start.isPending}
              onClick={() =>
                tier !== null &&
                start.mutate(
                  { scenarios: chosen, tier, prompt_version: prompt, cap_usd: capValue },
                  { onSettled: () => setConfirming(false) },
                )
              }
            >
              Spend up to {dollars(capValue)}: start
            </button>
            <button type="button" className="btn btn-quiet" onClick={() => setConfirming(false)}>
              Cancel
            </button>
          </>
        ) : (
          <button
            type="button"
            className="btn btn-secondary"
            disabled={chosen.length === 0 || tier === null || !capOk}
            onClick={() => setConfirming(true)}
          >
            Run {chosen.length} scenario{chosen.length === 1 ? "" : "s"}
          </button>
        )}
      </div>
    </div>
  );
}

function RunTable({ runs }: { runs: EvalRun[] }) {
  if (runs.length === 0) {
    return <p className="lens-note">No evaluation runs yet.</p>;
  }
  return (
    <div className="lens-table-wrap">
      <table className="lens-table">
        <thead>
          <tr>
            <th>Queued</th>
            <th>Scenario</th>
            <th>Status</th>
            <th>Tier, model</th>
            <th>Prompt</th>
            <th className="num">Turns</th>
            <th className="num">Hard failures</th>
            <th className="num">Soft failures</th>
            <th className="num">Spent of cap</th>
            <th className="num">Took</th>
            <th>Checks</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id}>
              <td>{moment(run.queued_at)}</td>
              <td>{run.scenario}</td>
              <td className={run.status === "failed" || run.hard_failures > 0 ? "lens-refused" : undefined}>
                {run.status}
                {run.stale ? ", stale" : ""}
                {run.error ? `: ${run.error}` : ""}
              </td>
              <td>
                {run.tier}, {run.model ?? "not yet"}
              </td>
              <td>{run.prompt_version}</td>
              <td className="num">{run.turns}</td>
              <td className="num">{run.hard_failures}</td>
              <td className="num">{run.soft_failures}</td>
              <td className="num">
                {dollars(run.cost_usd, run.unmetered_calls)} of {dollars(run.cap_usd)}
              </td>
              <td className="num">{milliseconds(run.duration_ms)}</td>
              <td>
                {run.checks.length === 0 ? (
                  ""
                ) : (
                  <details>
                    <summary>
                      {run.checks.length} check{run.checks.length === 1 ? "" : "s"}
                    </summary>
                    <ul>
                      {run.checks.map((check, index) => (
                        <li key={`${check.name}-${index}`} className={check.ok || !check.hard ? undefined : "lens-refused"}>
                          {check.ok ? "passed" : check.hard ? "failed" : "soft fail"}: {check.name}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Comparison({ report }: { report: ComparisonReport }) {
  const points = report.groups.flatMap((group) =>
    group.cost_per_run.value === null || group.clean_runs.value === null
      ? []
      : [{ name: group.name, cost: group.cost_per_run.value, clean: group.clean_runs.value * 100 }],
  );
  const scenarios = [...new Set(report.cells.map((cell) => cell.scenario))].sort();
  const names = report.groups.map((group) => group.name);
  return (
    <section className="lens-section">
      <h2 className="lens-heading">Accuracy against cost and latency</h2>
      <p className="lens-note">
        From completed evaluation runs only, by model and conduct prompt version. Accuracy is
        the scripted hard checks: the share of runs where none failed, and the share of hard
        checks that passed. Soft checks turn on judgement and are left out. Runs that were
        capped, failed or are still going have no finished transcript, so they are counted
        here and not scored: {report.left_out} of them.
      </p>
      <div className="lens-tiles">
        <Tile label="Completed runs" value={String(report.completed_runs)} />
        <Tile label="Left out" value={String(report.left_out)} />
        <Tile label="Models and prompts compared" value={String(report.groups.length)} />
      </div>
      <ChartCard
        title="Does a run that costs more pass its checks more often?"
        sample={
          points.length < TOO_FEW
            ? `${points.length} ${points.length === 1 ? "model and prompt" : "models and prompts"}: too few to read a trend from yet`
            : `${points.length} models and prompts, each point the median of its runs`
        }
        table={<GroupTable groups={report.groups} />}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
            <CartesianGrid stroke="var(--border)" />
            <XAxis
              type="number"
              dataKey="cost"
              name="Median cost per run, USD"
              {...axis}
              domain={["auto", "auto"]}
              tickFormatter={(v: number) => dollars(v)}
            />
            <YAxis
              type="number"
              dataKey="clean"
              name="Runs with no hard failure, %"
              {...axis}
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v}%`}
              width={44}
            />
            <Tooltip
              cursor={{ stroke: "var(--border)" }}
              content={(props) => (
                <LensTooltip
                  {...props}
                  format={(v) => new Intl.NumberFormat("en-GB", { maximumFractionDigits: 4 }).format(v)}
                  labelFormat={() => "One model and prompt"}
                />
              )}
            />
            <Scatter
              isAnimationActive={false}
              data={points}
              fill="var(--series-1)"
              stroke="var(--raised)"
              strokeWidth={2}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </ChartCard>
      {scenarios.length > 0 ? (
        <div className="lens-table-wrap">
          <table className="lens-table">
            <caption className="lens-note">
              Each scenario under each model and prompt: runs with no hard failure, of runs, and
              the median cost
            </caption>
            <thead>
              <tr>
                <th>Scenario</th>
                {names.map((name) => (
                  <th key={name}>{name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {scenarios.map((scenario) => (
                <tr key={scenario}>
                  <td>{scenario}</td>
                  {names.map((name) => {
                    const cell = report.cells.find((c) => c.scenario === scenario && c.group === name);
                    return (
                      <td key={name} className={cell && cell.clean_runs < cell.runs ? "lens-refused" : undefined}>
                        {cell
                          ? `${cell.clean_runs} of ${cell.runs} clean, ${middle(cell.cost_per_run, (v) => dollars(v))}`
                          : "not run"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      <AgreementTiles agreement={report.agreement} />
    </section>
  );
}

function GroupTable({ groups }: { groups: ComparisonGroup[] }) {
  return (
    <div className="lens-table-wrap">
      <table className="lens-table">
        <thead>
          <tr>
            <th>Model and prompt</th>
            <th className="num">Runs</th>
            <th>No hard failure</th>
            <th>Hard checks passed</th>
            <th>Median cost per run</th>
            <th>Median time</th>
            <th>Median turns</th>
            <th>Scenarios</th>
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => (
            <tr key={group.name}>
              <td>{group.name}</td>
              <td className="num">{group.runs}</td>
              <td>{rate(group.clean_runs)}</td>
              <td>{rate(group.hard_checks)}</td>
              <td>{middle(group.cost_per_run, (v) => dollars(v, group.unmetered_calls))}</td>
              <td>{middle(group.duration_ms, milliseconds)}</td>
              <td>{middle(group.turns, (v) => v.toFixed(1))}</td>
              <td>{group.scenarios.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AgreementTiles({ agreement }: { agreement: Agreement }) {
  return (
    <>
      <h3 className="lens-heading">Does Qwen disagreeing predict trouble?</h3>
      <p className="lens-note">
        Qwen3-0.6B reading the same prompt on this machine, never the internals of the hosted
        model. A reading counts where the hosted call succeeded and the engine checked it; the
        last two split accepted answers by how a person labelled them.
      </p>
      <div className="lens-tiles">
        <Tile label="Readings stored" value={String(agreement.analysed)} />
        <Tile label="Qwen picked the same tool" value={rate(agreement.agrees)} />
        <Tile label="Same tool, when the engine accepted" value={rate(agreement.when_accepted)} />
        <Tile label="Same tool, when the engine refused" value={rate(agreement.when_refused)} />
        <Tile label="Same tool, answer labelled supported" value={rate(agreement.on_supported)} />
        <Tile label="Same tool, answer labelled invented" value={rate(agreement.on_invented)} />
      </div>
    </>
  );
}
