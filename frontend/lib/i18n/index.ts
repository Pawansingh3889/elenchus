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
import { bn } from "./bn";
import { de } from "./de";
import { en, type Messages } from "./en";
import { es } from "./es";
import { fil } from "./fil";
import { fr } from "./fr";
import { he } from "./he";
import { hi } from "./hi";
import { pt } from "./pt";
import { ur } from "./ur";

// Labelled in the language itself: a reader looking for their own language is not
// helped by seeing it named in one they do not read. Direction is data rather than
// something each component works out, and three of these read right to left.
export const LOCALES = {
  en: { label: "English", dir: "ltr" },
  es: { label: "Español", dir: "ltr" },
  fr: { label: "Français", dir: "ltr" },
  de: { label: "Deutsch", dir: "ltr" },
  pt: { label: "Português", dir: "ltr" },
  fil: { label: "Filipino", dir: "ltr" },
  hi: { label: "हिन्दी", dir: "ltr" },
  bn: { label: "বাংলা", dir: "ltr" },
  ar: { label: "العربية", dir: "rtl" },
  he: { label: "עברית", dir: "rtl" },
  ur: { label: "اردو", dir: "rtl" },
} as const satisfies Record<string, { label: string; dir: "ltr" | "rtl" }>;

export type Locale = keyof typeof LOCALES;

const DICTIONARIES: Record<Locale, Messages> = { en, es, fr, de, pt, fil, hi, bn, ar, he, ur };

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
