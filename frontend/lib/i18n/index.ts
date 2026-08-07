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
import { de } from "./de";
import { en, type Messages } from "./en";
import { es } from "./es";
import { fil } from "./fil";
import { lt } from "./lt";
import { lv } from "./lv";
import { pl } from "./pl";
import { ro } from "./ro";

// Labelled in the language itself: a reader looking for their own language is not
// helped by seeing it named in one they do not read. Direction is data rather than
// something each component works out.
//
// Every locale here is currently left-to-right. `dir` stays because the alternative is
// deleting the RTL path and the logical properties throughout the stylesheet that exist
// to serve it, and then rebuilding both the day a right-to-left language is added back.
// The field costs nothing; re-deriving the layout from scratch would not.
//
// English is not one of the offered respondent languages so much as the one the app is
// authored in: `Messages` is derived from `en`, it is the fallback for an unknown tag,
// and the seeded content is written in it. It stays in the picker for that reason.
export const LOCALES = {
  en: { label: "English", dir: "ltr" },
  es: { label: "Español", dir: "ltr" },
  de: { label: "Deutsch", dir: "ltr" },
  pl: { label: "Polski", dir: "ltr" },
  lv: { label: "Latviešu", dir: "ltr" },
  lt: { label: "Lietuvių", dir: "ltr" },
  ro: { label: "Română", dir: "ltr" },
  fil: { label: "Filipino", dir: "ltr" },
} as const satisfies Record<string, { label: string; dir: "ltr" | "rtl" }>;

export type Locale = keyof typeof LOCALES;

const DICTIONARIES: Record<Locale, Messages> = { en, es, de, pl, lv, lt, ro, fil };

export const DEFAULT_LOCALE: Locale = "en";

export function isLocale(value: string): value is Locale {
  // hasOwn, not `in`: `in` walks the prototype chain, so inherited names like
  // "constructor" or "toString" would pass this guard and messagesFor would hand a
  // component Object.prototype's function where a Messages object belongs. The store
  // trusts this exact check to sanitise whatever localStorage holds.
  return Object.hasOwn(LOCALES, value);
}

export function messagesFor(locale: Locale): Messages {
  return DICTIONARIES[locale] ?? en;
}

export function dirFor(locale: Locale): "ltr" | "rtl" {
  return LOCALES[locale]?.dir ?? "ltr";
}

export type { Messages };
