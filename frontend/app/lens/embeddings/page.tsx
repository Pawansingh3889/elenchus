"use client";

import Link from "next/link";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
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
import { ApiError } from "@/lib/api";
import { dollars, milliseconds, moment, tokenCount, TOO_FEW } from "@/lib/lensFormat";
import { useLensScope } from "@/lib/lensScope";
import {
  useLensAnswerMap,
  useLensDuplicates,
  useLensGrounding,
  useLensThemes,
  useMe,
} from "@/lib/queries";
import type {
  DuplicateReport,
  EmbeddingCost,
  GroundingJudged,
  GroundingReport,
  MapPoint,
  MapQuestion,
  ThemeQuestion,
} from "@/lib/schemas";

/**
 * Embeddings: what respondents said, placed by meaning rather than by words, and what
 * that placing cost. Every text is embedded once and cached by its hash, so the tiles are
 * what this view spent just now, and a repeat view reads $0. The grounding section is the
 * measurement that decides whether meaning may overrule the word check at all.
 */
export default function EmbeddingsPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [scope] = useLensScope();
  const map = useLensAnswerMap(scope.surveyId, admin);
  // Themes and duplicates wait for the map, so on a fresh survey they read the vectors it
  // just paid for instead of embedding the same texts again in parallel. A map that failed
  // is not followed: the other two would fail the same way.
  const settled = map.isSuccess;
  const themes = useLensThemes(scope.surveyId, admin && settled);
  const duplicates = useLensDuplicates(scope.surveyId, admin && settled);
  const grounding = useLensGrounding(admin);
  const spent = total([map.data?.cost, themes.data?.cost, duplicates.data?.cost]);
  const model = map.data?.model ?? themes.data?.model ?? duplicates.data?.model;
  const surveyError = map.error ?? themes.error ?? duplicates.error;

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Embeddings</h1>
        </div>
        <p className="lens-provenance">
          Measured per view. The cost is what embedding the texts this view needed spent just
          now; texts the cache already held cost nothing. Reads one whole survey: the run
          filter does not narrow it.
        </p>

        {scope.surveyId === null ? (
          <p className="lens-note">
            Choose a survey above to map its answers, group its free text and find near
            duplicates.
          </p>
        ) : (
          <>
            {/* Switched off is a state of this deployment, not an outage, so it reads as a
                note rather than under the banner's "unavailable" title. */}
            {surveyError instanceof ApiError && surveyError.status === 503 ? (
              <p className="lens-note">{surveyError.message}</p>
            ) : (
              <ErrorBanner error={surveyError} />
            )}
            {spent ? (
              <div className="lens-tiles">
                <Tile label="Embedding model" value={model ?? "not reported"} />
                <Tile
                  label="Spent on this view"
                  value={dollars(spent.cost_usd, spent.unmetered_calls)}
                />
                <Tile label="Time embedding" value={milliseconds(spent.duration_ms)} />
                <Tile
                  label="Tokens embedded"
                  value={tokenCount(spent.prompt_tokens, spent.unmetered_calls)}
                />
                <Tile label="Texts embedded now" value={String(spent.embedded)} />
                <Tile label="Texts read from the cache" value={String(spent.cached)} />
              </div>
            ) : null}

            {map.data ? (
              <section className="lens-section">
                <h2 className="lens-heading">Answer map</h2>
                <p className="lens-note">
                  Each dot is a recorded answer, placed by the meaning of the message that
                  produced it. Dots close together said similar things; the axes have no units.
                  {map.data.unplaced > 0
                    ? ` ${map.data.unplaced} answers are left off: no respondent message came before them.`
                    : ""}
                </p>
                <div className="lens-grid-2">
                  {map.data.questions.map((question) => (
                    <MapCard key={question.position} question={question} />
                  ))}
                </div>
                {map.data.questions.length === 0 ? (
                  <p className="lens-note">No answers recorded in this survey yet.</p>
                ) : null}
              </section>
            ) : map.isFetching ? (
              <p className="lens-note">Embedding what respondents said…</p>
            ) : null}

            {themes.data ? <Themes questions={themes.data.questions} /> : null}
            {duplicates.data ? <Duplicates report={duplicates.data} /> : null}
          </>
        )}

        <ErrorBanner error={grounding.error} />
        {grounding.data ? <Grounding report={grounding.data} /> : null}
      </div>
    </Gate>
  );
}

/** The spend of every report loaded so far, or null before any has. */
function total(costs: (EmbeddingCost | undefined)[]): EmbeddingCost | null {
  const loaded = costs.filter((cost): cost is EmbeddingCost => cost !== undefined);
  if (loaded.length === 0) return null;
  return loaded.reduce((sum, cost) => ({
    texts: sum.texts + cost.texts,
    cached: sum.cached + cost.cached,
    embedded: sum.embedded + cost.embedded,
    calls: sum.calls + cost.calls,
    prompt_tokens: sum.prompt_tokens + cost.prompt_tokens,
    cost_usd: sum.cost_usd + cost.cost_usd,
    unmetered_calls: sum.unmetered_calls + cost.unmetered_calls,
    duration_ms: sum.duration_ms + cost.duration_ms,
  }));
}

/** The data's range plus a margin, so a dot at an extreme is drawn whole rather than
 *  halved by the plot's edge; with two answers, both of them are extremes. */
function padded(values: number[]): [number, number] {
  if (values.length === 0) return [-1, 1];
  const low = Math.min(...values);
  const high = Math.max(...values);
  const pad = high === low ? 1 : (high - low) * 0.12;
  return [low - pad, high + pad];
}

function MapCard({ question }: { question: MapQuestion }) {
  const n = question.points.length;
  return (
    <ChartCard
      title={question.text}
      sample={`${n} answers${n < TOO_FEW ? ", too few to read groups from" : ""}`}
      table={<MapTable question={question} />}
    >
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid stroke="var(--border)" />
          <XAxis type="number" dataKey="x" {...axis} tick={false} domain={padded(question.points.map((point) => point.x))} />
          <YAxis type="number" dataKey="y" {...axis} tick={false} width={8} domain={padded(question.points.map((point) => point.y))} />
          <Tooltip cursor={false} content={(props) => <PointTooltip active={props.active} payload={props.payload} />} />
          <Scatter isAnimationActive={false} data={question.points} fill="var(--series-1)" stroke="var(--raised)" strokeWidth={2} />
        </ScatterChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function PointTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: ReadonlyArray<{ payload?: MapPoint }>;
}) {
  const point = payload?.[0]?.payload;
  if (!active || !point) return null;
  return (
    <div className="lens-tooltip">
      <div className="lens-tooltip-label">Recorded: {point.recorded}</div>
      <div className="lens-tooltip-said">&ldquo;{point.said}&rdquo;</div>
    </div>
  );
}

function MapTable({ question }: { question: MapQuestion }) {
  const said = new Map(question.points.map((point) => [point.answer_id, point.said]));
  return (
    <table className="lens-table lens-table-prose">
      <thead>
        <tr>
          <th>Said</th>
          <th>Recorded</th>
          <th>Run</th>
          <th>Closest in meaning</th>
        </tr>
      </thead>
      <tbody>
        {question.points.map((point) => (
          <tr key={point.answer_id}>
            <td>{point.said}</td>
            <td>{point.recorded}</td>
            <td>
              <Link href={`/lens/runs/${point.run_id}`}>{point.run_id.slice(0, 8)}</Link>
            </td>
            <td>{point.neighbours.map((id) => said.get(id) ?? id.slice(0, 8)).join(" · ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Themes({ questions }: { questions: ThemeQuestion[] }) {
  return (
    <section className="lens-section">
      <h2 className="lens-heading">Themes in free text</h2>
      <p className="lens-note">
        Free-text answers grouped by meaning, largest group first, about one theme per three
        answers and never more than four. The quote shown is the answer nearest the middle of
        its group.
      </p>
      {questions.length === 0 ? (
        <p className="lens-note">No free-text answers in this survey.</p>
      ) : null}
      {questions.map((question) => (
        <div key={question.position} className="lens-table-wrap">
          <table className="lens-table lens-table-prose">
            <caption className="lens-note">
              {question.text} · {question.texts} answers
            </caption>
            <thead>
              <tr>
                <th className="num">Answers</th>
                <th className="num">Runs</th>
                <th>Nearest the middle</th>
                <th>Everything in it</th>
              </tr>
            </thead>
            <tbody>
              {question.themes.map((theme) => (
                <tr key={theme.representative}>
                  <td className="num">{theme.size}</td>
                  <td className="num">{theme.runs}</td>
                  <td>{theme.representative}</td>
                  <td>
                    <details>
                      <summary>{theme.members.length} answers</summary>
                      <ul>
                        {theme.members.map((member, index) => (
                          <li key={`${member}-${index}`}>{member}</li>
                        ))}
                      </ul>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}

function Duplicates({ report }: { report: DuplicateReport }) {
  return (
    <section className="lens-section">
      <h2 className="lens-heading">Near duplicates</h2>
      <p className="lens-note">
        Messages of three words or more, from different runs, whose meaning is at least{" "}
        {report.threshold} similar. {report.texts} messages compared. Copied answers show up
        here; so do two people who simply agree.
      </p>
      <div className="lens-table-wrap">
        <table className="lens-table lens-table-prose">
          <thead>
            <tr>
              <th>One run said</th>
              <th>Another run said</th>
              <th>Runs</th>
              <th className="num">Similarity</th>
            </tr>
          </thead>
          <tbody>
            {report.pairs.map((pair) => (
              <tr key={`${pair.first_run}-${pair.second_run}-${pair.first}-${pair.second}`}>
                <td>{pair.first}</td>
                <td>{pair.second}</td>
                <td>
                  <Link href={`/lens/runs/${pair.first_run}`}>{pair.first_run.slice(0, 8)}</Link>{" "}
                  · <Link href={`/lens/runs/${pair.second_run}`}>{pair.second_run.slice(0, 8)}</Link>
                </td>
                <td className="num">{pair.similarity.toFixed(3)}</td>
              </tr>
            ))}
            {report.pairs.length === 0 ? (
              <tr>
                <td colSpan={4} className="muted">
                  None above the threshold.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function signed(value: number | null): string {
  if (value === null) return "none";
  return `${value >= 0 ? "+" : ""}${value.toFixed(4)}`;
}

function Grounding({ report }: { report: GroundingReport }) {
  // Only the pairs the word check refused are decided by the margin; the rest never reach it.
  const decided = report.judged
    .filter((pair) => !pair.word_supported)
    .map((pair) => ({ ...pair, label: pair.supported ? "Real answer" : "Wrong answer" }));
  const recommended = report.recommended_margin;
  const live = report.semantic_enabled
    ? `on, margin ${report.configured_margin ?? "unset"}`
    : "off";

  return (
    <section className="lens-section">
      <h2 className="lens-heading">Grounding by meaning</h2>
      <p className="lens-provenance">
        Measured {moment(report.measured_at)} with {report.model} on {report.pairs} labelled
        pairs, {report.negatives}{" "}of them wrong answers. A choice the word check refuses counts
        as said only when it is the closest of its question&rsquo;s options to what was said,
        by the margin. Switched {live} in this deployment.
      </p>
      <div className="lens-tiles">
        <Tile
          label="Word check alone"
          value={`${report.word_false_accepts} wrong accepted, ${report.word_false_refusals} real refused`}
        />
        <Tile label="Recommended margin" value={recommended === null ? "none" : String(recommended)} />
        <Tile
          label="At the recommended margin"
          value={
            report.at_recommended_false_accepts === null
              ? "no margin passes"
              : `${report.at_recommended_false_accepts} wrong accepted, ${report.at_recommended_false_refusals} real refused`
          }
        />
        <Tile
          label="Headroom"
          value={`${signed(report.highest_negative_margin)} to ${signed(report.lowest_positive_margin)}`}
        />
      </div>

      <div className="lens-grid-2">
        <ChartCard
          title="Margin of each answer the word check refused"
          sample={`${decided.length} of ${report.pairs} pairs; the dashed line is the recommended margin`}
          table={<GroundingTable pairs={report.judged} />}
        >
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis
                type="number"
                dataKey="margin"
                {...axis}
                domain={["auto", "auto"]}
                tickFormatter={(value: number) => value.toFixed(2)}
              />
              <YAxis
                type="category"
                dataKey="label"
                {...axis}
                width={96}
                allowDuplicatedCategory={false}
              />
              <Tooltip
                cursor={false}
                content={(props) => <JudgedTooltip active={props.active} payload={props.payload} />}
              />
              {recommended !== null ? (
                <ReferenceLine x={recommended} stroke="var(--ink)" strokeDasharray="4 4" />
              ) : null}
              <Scatter isAnimationActive={false} data={decided} fill="var(--series-1)" stroke="var(--raised)" strokeWidth={2} />
            </ScatterChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Mistakes at each margin"
          sample={`${report.sweep.length} margins swept; wrong answers include ${report.word_false_accepts} the word check accepts, which no margin reaches`}
          legend={[
            { label: "Wrong answers accepted", color: "var(--series-1)" },
            { label: "Real answers refused", color: "var(--series-2)" },
          ]}
          table={<SweepTable report={report} />}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={report.sweep} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis
                type="number"
                dataKey="margin"
                {...axis}
                domain={["dataMin", "dataMax"]}
                tickFormatter={(value: number) => value.toFixed(2)}
              />
              <YAxis {...axis} allowDecimals={false} width={32} />
              <Tooltip
                content={(props) => (
                  <LensTooltip
                    {...props}
                    format={(value) => String(value)}
                    labelFormat={(label) => `margin ${Number(label).toFixed(2)}`}
                  />
                )}
              />
              {recommended !== null ? (
                <ReferenceLine x={recommended} stroke="var(--ink)" strokeDasharray="4 4" />
              ) : null}
              <Line isAnimationActive={false} type="stepAfter" dataKey="false_accepts" name="Wrong answers accepted" stroke="var(--series-1)" strokeWidth={2} dot={false} />
              <Line isAnimationActive={false} type="stepAfter" dataKey="false_refusals" name="Real answers refused" stroke="var(--series-2)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </section>
  );
}

function JudgedTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: ReadonlyArray<{ payload?: GroundingJudged }>;
}) {
  const pair = payload?.[0]?.payload;
  if (!active || !pair) return null;
  return (
    <div className="lens-tooltip">
      <div className="lens-tooltip-label">
        {pair.supported ? "Real answer" : "Wrong answer"} · margin {signed(pair.margin)}
      </div>
      <div className="lens-tooltip-said">&ldquo;{pair.said}&rdquo;</div>
      <div className="lens-tooltip-name">chosen: {pair.option}</div>
    </div>
  );
}

function GroundingTable({ pairs }: { pairs: GroundingJudged[] }) {
  return (
    <table className="lens-table lens-table-prose">
      <thead>
        <tr>
          <th>Said</th>
          <th>Chosen</th>
          <th>Language</th>
          <th>Label</th>
          <th>Word check</th>
          <th className="num">Similarity</th>
          <th className="num">Margin</th>
        </tr>
      </thead>
      <tbody>
        {pairs.map((pair, index) => (
          <tr key={`${pair.said}-${pair.option}-${index}`}>
            <td>{pair.said}</td>
            <td>{pair.option}</td>
            <td>{pair.language}</td>
            <td>{pair.supported ? "real" : "wrong"}</td>
            <td className={pair.word_supported ? undefined : "lens-refused"}>
              {pair.word_supported ? "accepts" : "refuses"}
            </td>
            <td className="num">{pair.similarity.toFixed(3)}</td>
            <td className="num">{signed(pair.margin)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SweepTable({ report }: { report: GroundingReport }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th className="num">Margin</th>
          <th className="num">Wrong answers accepted</th>
          <th className="num">Real answers refused</th>
        </tr>
      </thead>
      <tbody>
        {report.sweep.map((row) => (
          <tr key={row.margin}>
            <td className="num">{row.margin.toFixed(2)}</td>
            <td className="num">{row.false_accepts}</td>
            <td className="num">{row.false_refusals}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
