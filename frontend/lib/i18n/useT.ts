"use client";

import { useEffect } from "react";

import { useLocaleStore } from "../store";
import { dirFor, messagesFor, type Messages } from "./index";

/**
 * The strings for the active locale.
 *
 * Named `useT` rather than `t` because it reads the store, so it is a hook and has to
 * look like one. Components destructure the area they need:
 *
 *     const { builder } = useT();
 *     <button>{builder.addQuestion}</button>
 */
export function useT(): Messages {
  return messagesFor(useLocaleStore((s) => s.locale));
}

/**
 * Keep `<html lang>` and `<html dir>` in step with the chosen locale.
 *
 * Done from the client because the locale lives in a persisted store rather than the
 * URL, and the root layout is a server component that cannot read it. `lang` is not
 * decoration: it drives the per-script line-height and font stacks in globals.css, and
 * it is what a screen reader uses to choose a voice. `dir` is what mirrors the layout,
 * which the logical properties throughout the stylesheet were written to support.
 */
export function useDocumentLanguage(): void {
  const locale = useLocaleStore((s) => s.locale);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = dirFor(locale);
  }, [locale]);
}
