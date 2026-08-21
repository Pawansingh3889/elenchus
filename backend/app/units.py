"""Unit handling for numeric questions: what a value means, and how to show it in another.

A question about temperature or a measurement is meaningless without its unit, which is
the bug that put "the temperature question had no unit" on the list. An author sets a
``unit`` and, optionally, a ``display_unit`` to also show (e.g. a freezer logged in
Celsius, read by someone who thinks in Fahrenheit). The converter turns one into the
other so the respondent sees both live, and the results keep the author's unit.

Temperature, length, mass and volume are pure formulas, so conversion is exact and needs
no network. Currency is deliberately absent: an exchange rate is not a formula, it is a
feed, and wiring one in is its own decision (source, caching, a failure mode). When that
lands, ``_UNITS`` gains a ``currency`` dimension and ``convert`` needs a rate table;
nothing else here changes.

Each unit is (dimension, factor_to_base, offset_to_base) where
``base = value * factor + offset``. Linear units have offset 0; temperature does not.
``K``/metre/kilogram/litre are the bases.
"""

from dataclasses import dataclass

# dimension -> (factor to base, offset to base). base value = value * factor + offset.
_UNITS: dict[str, tuple[str, float, float]] = {
    # Temperature, base Kelvin.
    "K": ("temperature", 1.0, 0.0),
    "C": ("temperature", 1.0, 273.15),
    "F": ("temperature", 5.0 / 9.0, 273.15 - 32.0 * 5.0 / 9.0),
    # Length, base metre.
    "m": ("length", 1.0, 0.0),
    "cm": ("length", 0.01, 0.0),
    "mm": ("length", 0.001, 0.0),
    "km": ("length", 1000.0, 0.0),
    "in": ("length", 0.0254, 0.0),
    "ft": ("length", 0.3048, 0.0),
    "mi": ("length", 1609.344, 0.0),
    # Mass, base kilogram.
    "kg": ("mass", 1.0, 0.0),
    "g": ("mass", 0.001, 0.0),
    "mg": ("mass", 1e-6, 0.0),
    "t": ("mass", 1000.0, 0.0),
    "lb": ("mass", 0.45359237, 0.0),
    "oz": ("mass", 0.028349523125, 0.0),
    # Volume, base litre.
    "l": ("volume", 1.0, 0.0),
    "ml": ("volume", 0.001, 0.0),
    "gal": ("volume", 3.785411784, 0.0),
}

DIMENSION_LABELS: dict[str, str] = {
    "temperature": "Temperature",
    "length": "Length",
    "mass": "Mass",
    "volume": "Volume",
}

# How a unit reads when shown to a human. Most are the bare symbol; temperature gets the
# degree sign so "32 C" is not mistaken for a count.
UNIT_LABELS: dict[str, str] = {
    "C": "°C",
    "F": "°F",
    "K": "K",
    "m": "m",
    "cm": "cm",
    "mm": "mm",
    "km": "km",
    "in": "in",
    "ft": "ft",
    "mi": "mi",
    "kg": "kg",
    "g": "g",
    "mg": "mg",
    "t": "t",
    "lb": "lb",
    "oz": "oz",
    "l": "L",
    "ml": "mL",
    "gal": "gal",
}


def unit_symbol(unit: str) -> str:
    return UNIT_LABELS.get(unit, unit)


def is_known_unit(unit: str | None) -> bool:
    return unit in _UNITS


def unit_dimension(unit: str) -> str | None:
    entry = _UNITS.get(unit)
    return entry[0] if entry else None


def can_convert(frm: str | None, to: str | None) -> bool:
    """Both units known, same dimension, and not identical (no point showing 5 m = 5 m)."""
    if not frm or not to or frm == to:
        return False
    dim_f = unit_dimension(frm)
    return dim_f is not None and dim_f == unit_dimension(to)


def convert(value: float, frm: str, to: str) -> float:
    """Convert ``value`` from ``frm`` to ``to``. Raises ValueError if they are not
    convertible (unknown unit, or different dimensions)."""
    f = _UNITS.get(frm)
    t = _UNITS.get(to)
    if f is None or t is None or f[0] != t[0]:
        raise ValueError(f"cannot convert {frm!r} to {to!r}")
    base = value * f[1] + f[2]
    return (base - t[2]) / t[1]


def _format(value: float) -> str:
    """Compact, human number: integers stay integers, others get a few significant figures."""
    if value == int(value):
        return str(int(value))
    return f"{value:.4g}"


def conversion_label(value: float, frm: str, to: str) -> str | None:
    """``"32 °C = 89.6 °F"`` for a convertible pair, or None when there is nothing to show."""
    if not can_convert(frm, to):
        return None
    return (
        f"{_format(value)} {unit_symbol(frm)} = "
        f"{_format(convert(value, frm, to))} {unit_symbol(to)}"
    )


@dataclass(frozen=True)
class UnitChoice:
    value: str
    label: str
    dimension: str


def unit_choices() -> list[UnitChoice]:
    """Every unit, for a grouped dropdown, in a stable dimension/label order."""
    order = ["temperature", "length", "mass", "volume"]
    choices = [UnitChoice(value=u, label=u, dimension=dim) for u, (dim, _, _) in _UNITS.items()]
    choices.sort(key=lambda c: (order.index(c.dimension), c.label))
    return choices
