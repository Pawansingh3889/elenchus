/**
 * How the interpretability pages group a prompt and write what a local model read in it.
 *
 * A prompt has one system prompt, one block of tool definitions, a transcript and the chat
 * template's own tokens. The pages group sections that way so a chart has five parts
 * rather than one per message, and the last thing the respondent said is kept apart,
 * because it is the part a reader most wants to see weighed.
 */

import type { PromptSection } from "./schemas";

export type PromptGroup = "system" | "tools" | "earlier" | "last" | "template";

export const GROUPS: { key: PromptGroup; label: string; color: string }[] = [
  { key: "system", label: "System prompt", color: "var(--series-1)" },
  { key: "tools", label: "Tool definitions", color: "var(--series-2)" },
  { key: "earlier", label: "Earlier transcript", color: "var(--series-3)" },
  { key: "last", label: "Last respondent message", color: "var(--series-4)" },
  // The reserved colour, not a fifth hue: four is what the palette validates for.
  { key: "template", label: "Chat template", color: "var(--series-other)" },
];

export const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)"];

/** Which group each section of this prompt belongs to. */
export function groupsOf(sections: PromptSection[]): Map<string, PromptGroup> {
  const lastUser = [...sections].reverse().find((s) => s.kind === "message" && s.role === "user");
  const groups = new Map<string, PromptGroup>();
  for (const section of sections) {
    if (section.kind === "system") groups.set(section.key, "system");
    else if (section.kind === "tools") groups.set(section.key, "tools");
    else if (section.kind === "template") groups.set(section.key, "template");
    else groups.set(section.key, section.key === lastUser?.key ? "last" : "earlier");
  }
  return groups;
}

/** Values keyed by section, summed into groups. A section the prompt does not name is a
 *  broken contract between the service and this page, and is thrown rather than dropped. */
export function byGroup(
  values: Record<string, number>,
  groups: Map<string, PromptGroup>,
): Record<PromptGroup, number> {
  const out: Record<PromptGroup, number> = { system: 0, tools: 0, earlier: 0, last: 0, template: 0 };
  for (const [key, value] of Object.entries(values)) {
    const group = groups.get(key);
    if (group === undefined) throw new Error(`The analysis names a section its prompt lacks: ${key}`);
    out[group] += value;
  }
  return out;
}

/** A probability as a percentage, keeping a small one visible instead of rounding it to 0. */
export function probability(value: number | null): string {
  if (value === null) return "not read";
  if (value > 0 && value < 0.001) return "under 0.1%";
  return `${(value * 100).toFixed(1)}%`;
}

/** The first layer from which the leading tool stays the model's final pick, or null. */
export function settlesAt(
  layers: { layer: number; tool_probabilities: Record<string, number> }[],
  pick: string,
): number | null {
  let settled: number | null = null;
  for (const layer of layers) {
    const leader = Object.entries(layer.tool_probabilities).sort((a, b) => b[1] - a[1])[0]?.[0];
    if (leader === pick) settled = settled ?? layer.layer;
    else settled = null;
  }
  return settled;
}

/** A token as text a reader can see, with spaces and line breaks made visible. */
export function visible(text: string): string {
  return JSON.stringify(text).slice(1, -1) || "(empty)";
}
