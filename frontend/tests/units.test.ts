import { describe, expect, it } from "vitest";

import {
  canConvert,
  convert,
  conversionLabel,
  isKnownUnit,
  unitSymbol,
} from "@/lib/units";

describe("units", () => {
  it("knows its units", () => {
    expect(isKnownUnit("C")).toBe(true);
    expect(isKnownUnit("banana")).toBe(false);
  });

  it("converts temperature both ways", () => {
    expect(convert(0, "C", "F")).toBeCloseTo(32, 6);
    expect(convert(100, "C", "F")).toBeCloseTo(212, 6);
    expect(convert(32, "F", "C")).toBeCloseTo(0, 6);
    // round trip back to Celsius
    expect(convert(convert(0, "C", "F"), "F", "C")).toBeCloseTo(0, 6);
  });

  it("converts length and mass", () => {
    expect(convert(1, "km", "m")).toBeCloseTo(1000, 6);
    expect(convert(12, "in", "cm")).toBeCloseTo(30.48, 3);
    expect(convert(1, "t", "kg")).toBeCloseTo(1000, 6);
    expect(convert(1, "gal", "l")).toBeCloseTo(3.785412, 6);
  });

  it("only converts within a dimension", () => {
    expect(canConvert("C", "F")).toBe(true);
    expect(canConvert("m", "ft")).toBe(true);
    expect(canConvert("C", "m")).toBe(false);
    expect(canConvert("m", "m")).toBe(false);
  });

  it("renders a label with degree signs", () => {
    expect(conversionLabel(32, "C", "F")).toBe("32 °C = 89.6 °F");
    expect(conversionLabel(5, "m", "C")).toBeNull();
  });

  it("symbols read naturally", () => {
    expect(unitSymbol("C")).toBe("°C");
    expect(unitSymbol("F")).toBe("°F");
    expect(unitSymbol("m")).toBe("m");
  });
});
