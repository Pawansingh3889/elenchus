"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
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
import { probability, SERIES, settlesAt, visible } from "@/lib/interpFormat";
import { dollars, milliseconds } from "@/lib/lensFormat";
import { useSelectedAsk } from "@/lib/lensScope";
import { useInterpAnalysis, useMe } from "@/lib/queries";
import type { StoredAnalysis } from "@/lib/schemas";

const OTHER = "Other tools";

/**
 * Hidden layers: at the moment Qwen3-0.6B is about to write a tool's name, each layer's
 * state read through the model's own output head, as a leaning between the offered tools.
 */
export default function HiddenLayersPage() {
  const { data: me, isLoading } = useMe();
  const admin = me?.is_admin === true;
  const [selected] = useSelectedAsk();
  const analysis = useInterpAnalysis(selected, admin);

  return (
    <Gate admin={admin} loading={isLoading}>
      <div className="page lens">
        <div className="page-head">
          <h1>Hidden layers</h1>
        </div>
        <p className="lens-provenance">
          Qwen3-0.6B reading the exact prompt a hosted call was sent. This is how a small open
          model reads that prompt, never the hosted model&rsquo;s internals. At the moment the
          tool&rsquo;s name is about to be written, every layer&rsquo;s state is passed through the
          model&rsquo;s own final norm and output head, the logit lens, and read as a leaning
          between the tools that were offered.
        </p>
        <InterpAsks admin={admin} need="reading" />
        <ErrorBanner error={analysis.error} />
        <ChosenReading selected={selected} loading={analysis.isFetching} stored={analysis.data}>
          {(stored) => <Layers stored={stored} />}
        </ChosenReading>
      </div>
    </Gate>
  );
}

function Layers({ stored }: { stored: StoredAnalysis }) {
  const reading = stored.analysis;
  const hosted = stored.target_tool;
  const offered = reading.tools.map((tool) => tool.name);
  // The most likely tools get a line each, always including the hosted pick; colour follows
  // the tool's place in the offered list, so a tool keeps its colour between calls.
  const likely = [...reading.tools].sort((a, b) => b.probability - a.probability).map((t) => t.name);
  const shown = likely.slice(0, SERIES.length);
  if (hosted !== null && offered.includes(hosted) && !shown.includes(hosted)) {
    shown[SERIES.length - 1] = hosted;
  }
  shown.sort((a, b) => offered.indexOf(a) - offered.indexOf(b));
  const folded = offered.filter((name) => !shown.includes(name));
  const rows = reading.layers.map((layer) => {
    const row: Record<string, number | string> = { layer: layer.layer, norm: layer.norm };
    for (const name of shown) row[name] = layer.tool_probabilities[name];
    if (folded.length > 0) {
      row[OTHER] = folded.reduce((sum, name) => sum + layer.tool_probabilities[name], 0);
    }
    return row;
  });
  const settle = settlesAt(reading.layers, reading.pick);
  const onHosted = hosted === null ? null : (reading.tools.find((t) => t.name === hosted)?.probability ?? null);
  const legend = [
    ...shown.map((name, index) => ({ label: name, color: SERIES[index] })),
    ...(folded.length > 0 ? [{ label: OTHER, color: "var(--series-other)" }] : []),
  ];

  return (
    <>
      <div className="lens-tiles">
        <Tile label="Hosted model called" value={hosted ?? "no checked call"} />
        <Tile label="Qwen's pick" value={reading.pick} />
        <Tile label="Qwen on the hosted pick" value={probability(onHosted)} />
        <Tile
          label="Settles on its pick"
          value={settle === null ? "never" : `layer ${settle} of ${reading.layers.length}`}
        />
        <Tile label="Calls a tool at all" value={probability(reading.calls_a_tool)} />
        <Tile label="Reading took" value={milliseconds(stored.duration_ms)} />
        <Tile label="Reading cost" value={dollars(stored.cost_usd)} />
        <Tile
          label="The hosted call"
          value={`${milliseconds(stored.hosted_ms)} · ${dollars(stored.hosted_cost_usd)}`}
        />
      </div>

      <div className="lens-grid-2">
        <ChartCard
          title="Leaning between the offered tools, layer by layer"
          sample={`${reading.layers.length} layers, ${reading.prompt_tokens} prompt tokens; the dashed line is where it settles`}
          legend={legend}
          table={<LayerTable stored={stored} shown={shown} folded={folded} />}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis dataKey="layer" type="number" domain={[1, reading.layers.length]} {...axis} />
              <YAxis domain={[0, 1]} {...axis} width={44} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} />
              <Tooltip
                content={(props) => (
                  <LensTooltip {...props} format={probability} labelFormat={(label) => `layer ${String(label)}`} />
                )}
              />
              {settle !== null ? <ReferenceLine x={settle} stroke="var(--ink)" strokeDasharray="4 4" /> : null}
              {shown.map((name, index) => (
                <Line key={name} isAnimationActive={false} type="linear" dataKey={name} name={name} stroke={SERIES[index]} strokeWidth={2} dot={false} />
              ))}
              {folded.length > 0 ? (
                <Line isAnimationActive={false} type="linear" dataKey={OTHER} name={OTHER} stroke="var(--series-other)" strokeWidth={2} dot={false} />
              ) : null}
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Size of the state at that moment, layer by layer"
          sample="The length of the hidden state vector at the decision point"
          table={<NormTable stored={stored} />}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis dataKey="layer" type="number" domain={[1, reading.layers.length]} {...axis} />
              <YAxis {...axis} width={52} />
              <Tooltip
                content={(props) => (
                  <LensTooltip {...props} format={(v) => v.toFixed(1)} labelFormat={(label) => `layer ${String(label)}`} />
                )}
              />
              <Line isAnimationActive={false} type="linear" dataKey="norm" name="State size" stroke="var(--series-1)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </>
  );
}

function LayerTable({ stored, shown, folded }: { stored: StoredAnalysis; shown: string[]; folded: string[] }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th className="num">Layer</th>
          {shown.map((name) => (
            <th key={name} className="num">
              {name}
            </th>
          ))}
          {folded.length > 0 ? <th className="num">{OTHER}</th> : null}
          <th>Top token</th>
        </tr>
      </thead>
      <tbody>
        {stored.analysis.layers.map((layer) => (
          <tr key={layer.layer}>
            <td className="num">{layer.layer}</td>
            {shown.map((name) => (
              <td key={name} className="num">
                {probability(layer.tool_probabilities[name])}
              </td>
            ))}
            {folded.length > 0 ? (
              <td className="num">
                {probability(folded.reduce((sum, name) => sum + layer.tool_probabilities[name], 0))}
              </td>
            ) : null}
            <td>{visible(layer.top_token)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function NormTable({ stored }: { stored: StoredAnalysis }) {
  return (
    <table className="lens-table">
      <thead>
        <tr>
          <th className="num">Layer</th>
          <th className="num">State size</th>
        </tr>
      </thead>
      <tbody>
        {stored.analysis.layers.map((layer) => (
          <tr key={layer.layer}>
            <td className="num">{layer.layer}</td>
            <td className="num">{layer.norm.toFixed(1)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
