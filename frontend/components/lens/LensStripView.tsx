import type { LensStrip } from "@/lib/schemas";
import { dollars, milliseconds, tokenCount } from "@/lib/lensFormat";

/**
 * The strip every lens page carries: what all traced turns cost, and per tier where the
 * time went. Latency and first-token time sit side by side because their gap is the time
 * spent writing; the rest was the model reading the prompt and thinking.
 */
export function LensStripView({ strip }: { strip: LensStrip }) {
  return (
    <section className="lens-section">
      <div className="lens-tiles">
        <Tile label="Runs traced" value={numbersOf(strip.runs)} />
        <Tile label="Turns" value={numbersOf(strip.turns)} />
        <Tile label="Median turn" value={milliseconds(strip.turn_ms_p50)} />
        <Tile label="Retries" value={numbersOf(strip.retries)} />
      </div>
      <div className="lens-table-wrap">
        <table className="lens-table">
          <thead>
            <tr>
              <th>Tier and model</th>
              <th className="num">Attempts</th>
              <th className="num">Failed</th>
              <th className="num">Tokens in</th>
              <th className="num">of which cached</th>
              <th className="num">Tokens out</th>
              <th className="num">of which reasoning</th>
              <th className="num">Cost</th>
              <th className="num">Latency p50 / p95</th>
              <th className="num">First token p50 / p95</th>
            </tr>
          </thead>
          <tbody>
            {strip.tiers.map((tier) => (
              <tr key={`${tier.tier}-${tier.model}`}>
                <td>
                  tier {tier.tier ?? "?"} · {tier.model ?? "unknown model"}
                </td>
                <td className="num">{numbersOf(tier.attempts)}</td>
                <td className="num">{numbersOf(tier.failed_attempts)}</td>
                <td className="num">{tokenCount(tier.prompt_tokens, tier.unmetered_attempts)}</td>
                <td className="num">{tokenCount(tier.cached_tokens, tier.unmetered_attempts)}</td>
                <td className="num">
                  {tokenCount(tier.completion_tokens, tier.unmetered_attempts)}
                </td>
                <td className="num">
                  {tokenCount(tier.reasoning_tokens, tier.unmetered_attempts)}
                </td>
                <td className="num">{dollars(tier.cost_usd, tier.unmetered_attempts)}</td>
                <td className="num">
                  {milliseconds(tier.latency_ms_p50)} / {milliseconds(tier.latency_ms_p95)}
                </td>
                <td className="num">
                  {milliseconds(tier.first_token_ms_p50)} /{" "}
                  {milliseconds(tier.first_token_ms_p95)}
                </td>
              </tr>
            ))}
            {strip.tiers.length === 0 ? (
              <tr>
                <td colSpan={10} className="muted">
                  No model calls traced yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function numbersOf(value: number): string {
  return new Intl.NumberFormat("en-GB").format(value);
}

export function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="lens-tile">
      <div className="lens-tile-label">{label}</div>
      <div className="lens-tile-value">{value}</div>
    </div>
  );
}
