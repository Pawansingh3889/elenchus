/**
 * The locale registry: which languages exist, which read right-to-left, and how a
 * component gets its strings.
 *
 * No i18n library. The app has around eighty strings and one plural form in use, which
 * a library would cover at the cost of a runtime, a message format to learn, and
 * translations that are no longer type-checked. `Messages` being derived from English
 * is the property worth keeping: a locale missing a key fails `tsc`, so a half-finished
 * translation cannot ship as blank labels.
 */
import { ar } from "./ar";
import { en, type Messages } from "./en";
import { es } from "./es";

export const LOCALES = {
  en: { label: "English", dir: "ltr" },
  es: { label: "Español", dir: "ltr" },
  ar: { label: "العربية", dir: "rtl" },
} as const satisfies Record<string, { label: string; dir: "ltr" | "rtl" }>;

export type Locale = keyof typeof LOCALES;

const DICTIONARIES: Record<Locale, Messages> = { en, es, ar };

export const DEFAULT_LOCALE: Locale = "en";

export function isLocale(value: string): value is Locale {
  return value in LOCALES;
}

export function messagesFor(locale: Locale): Messages {
  return DICTIONARIES[locale] ?? en;
}

export function dirFor(locale: Locale): "ltr" | "rtl" {
  return LOCALES[locale]?.dir ?? "ltr";
}

export type { Messages };
