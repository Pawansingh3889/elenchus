// Client-side mirror of backend/app/units.py. Pure formula, no network, so the
// respondent sees a live conversion as they type. Keep the factors/offsets in step with
// the backend: the values stored are plain numbers, but the labels the author and
// respondent read must agree. Currency is intentionally absent (rates need a feed).

export type Dimension = "temperature" | "length" | "mass" | "volume";

type UnitDef = { dimension: Dimension; factor: number; offset: number };

const UNITS: Record<string, UnitDef> = {
  // Temperature, base Kelvin.
  K: { dimension: "temperature", factor: 1, offset: 0 },
  C: { dimension: "temperature", factor: 1, offset: 273.15 },
  F: { dimension: "temperature", factor: 5 / 9, offset: 273.15 - (32 * 5) / 9 },
  // Length, base metre.
  m: { dimension: "length", factor: 1, offset: 0 },
  cm: { dimension: "length", factor: 0.01, offset: 0 },
  mm: { dimension: "length", factor: 0.001, offset: 0 },
  km: { dimension: "length", factor: 1000, offset: 0 },
  in: { dimension: "length", factor: 0.0254, offset: 0 },
  ft: { dimension: "length", factor: 0.3048, offset: 0 },
  mi: { dimension: "length", factor: 1609.344, offset: 0 },
  // Mass, base kilogram.
  kg: { dimension: "mass", factor: 1, offset: 0 },
  g: { dimension: "mass", factor: 0.001, offset: 0 },
  mg: { dimension: "mass", factor: 1e-6, offset: 0 },
  t: { dimension: "mass", factor: 1000, offset: 0 },
  lb: { dimension: "mass", factor: 0.45359237, offset: 0 },
  oz: { dimension: "mass", factor: 0.028349523125, offset: 0 },
  // Volume, base litre.
  l: { dimension: "volume", factor: 1, offset: 0 },
  ml: { dimension: "volume", factor: 0.001, offset: 0 },
  gal: { dimension: "volume", factor: 3.785411784, offset: 0 },
};

const UNIT_SYMBOLS: Record<string, string> = {
  C: "°C",
  F: "°F",
  K: "K",
  m: "m",
  cm: "cm",
  mm: "mm",
  km: "km",
  in: "in",
  ft: "ft",
  mi: "mi",
  kg: "kg",
  g: "g",
  mg: "mg",
  t: "t",
  lb: "lb",
  oz: "oz",
  l: "L",
  ml: "mL",
  gal: "gal",
};

const DIMENSION_ORDER: Dimension[] = ["temperature", "length", "mass", "volume"];

export function isKnownUnit(unit: string | null | undefined): boolean {
  return !!unit && unit in UNITS;
}

export function unitDimension(unit: string | null | undefined): Dimension | null {
  const def = unit ? UNITS[unit] : undefined;
  return def ? def.dimension : null;
}

export function canConvert(from: string | null | undefined, to: string | null | undefined): boolean {
  if (!from || !to || from === to) return false;
  const a = UNITS[from];
  const b = UNITS[to];
  return !!a && !!b && a.dimension === b.dimension;
}

export function convert(value: number, from: string, to: string): number {
  const f = UNITS[from];
  const t = UNITS[to];
  if (!f || !t || f.dimension !== t.dimension) {
    throw new Error(`cannot convert ${from} to ${to}`);
  }
  const base = value * f.factor + f.offset;
  return (base - t.offset) / t.factor;
}

function formatValue(value: number): string {
  if (Number.isInteger(value)) return String(value);
  return value.toPrecision(4).replace(/\.?0+$/, "");
}

export function unitSymbol(unit: string | null | undefined): string {
  if (!unit) return "";
  return UNIT_SYMBOLS[unit] ?? unit;
}

export function conversionLabel(value: number, from: string, to: string): string | null {
  if (!canConvert(from, to)) return null;
  return `${formatValue(value)} ${unitSymbol(from)} = ${formatValue(convert(value, from, to))} ${unitSymbol(to)}`;
}

export interface UnitChoice {
  value: string;
  label: string;
  dimension: Dimension;
}

export function unitChoices(): UnitChoice[] {
  const choices: UnitChoice[] = Object.entries(UNITS).map(([value, def]) => ({
    value,
    label: unitSymbol(value),
    dimension: def.dimension,
  }));
  choices.sort(
    (a, b) =>
      DIMENSION_ORDER.indexOf(a.dimension) - DIMENSION_ORDER.indexOf(b.dimension) ||
      a.label.localeCompare(b.label),
  );
  return choices;
}

export function unitsByDimension(): Record<Dimension, UnitChoice[]> {
  const grouped = {} as Record<Dimension, UnitChoice[]>;
  for (const dim of DIMENSION_ORDER) grouped[dim] = [];
  for (const choice of unitChoices()) grouped[choice.dimension].push(choice);
  return grouped;
}
