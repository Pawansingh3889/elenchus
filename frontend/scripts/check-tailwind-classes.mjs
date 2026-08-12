/**
 * Every Tailwind class named in the source must actually produce CSS.
 *
 * This exists because of a failure that no other gate here can see. `tsc` and
 * `eslint` both read a className as a string, so an invented utility is not a type
 * error and not a lint error: it is a correct string that compiles to nothing, and
 * the element silently renders without the style. Two were written on the day this
 * guard was added (`inset-inline-end-3` and `inset-inline-0`, neither of which is a
 * Tailwind class; the real ones are `end-3` and `start-0 end-0`), and both passed
 * the whole frontend gate.
 *
 * It reads the same entry stylesheet the app does, so it knows about every token
 * declared in the @theme block and cannot disagree with the build about what exists.
 *
 * Only string literals are checked. A class assembled at runtime is invisible here,
 * which is a real limit and the reason this is a guard rather than a proof.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

import { compile } from "tailwindcss";

const ROOT = path.resolve(import.meta.dirname, "..");
const require = createRequire(path.join(ROOT, "package.json"));
const SOURCE_DIRS = ["app", "components", "lib"];
// The translation catalogues are prose in eight languages and contain no classes at
// all, so every class-shaped word in them is a false positive by construction.
const SKIP = [path.join("lib", "i18n")];

/** Class-shaped tokens, read only where classes can legitimately appear.
 *
 * Scoped to `className=…`, `cva(…)` and `cn(…)` rather than to every string in the
 * file. Reading every literal turned up import specifiers, query keys and
 * localStorage keys, all of which are kebab-case and none of which is a class; the
 * noise was large enough to bury a real finding, which is the only thing this is for.
 */
function classNamesIn(source) {
  const found = new Set();
  const regions = [];
  // className="…" and className={ … } up to the closing brace of the expression, plus
  // the argument lists of cn() and cva(). Brace matching is deliberately shallow: a
  // className expression that nests braces is rare and the worst case is reading a
  // little less than everything, never reporting something that is not there.
  for (const match of source.matchAll(/className\s*=\s*"([^"]*)"/g)) regions.push(match[1]);
  for (const match of source.matchAll(/className\s*=\s*\{([\s\S]*?)\}\s*\n?\s*(?:\/?>|\w+=)/g)) {
    regions.push(match[1]);
  }
  for (const match of source.matchAll(/\bcva\(([\s\S]*?)\n\);/g)) regions.push(match[1]);
  for (const match of source.matchAll(/\bcn\(([\s\S]*?)\)/g)) regions.push(match[1]);

  for (const region of regions) {
    for (const [, literal] of region.matchAll(/"([^"\\\n]*)"/g)) {
      for (const token of literal.split(/\s+/)) {
        if (!token || token !== token.toLowerCase()) continue;
        if (!/^[a-z0-9]/.test(token)) continue;
        // A CSS var handed to a chart library, not a class.
        if (token.startsWith("var(") || token.startsWith("calc(")) continue;
        if (!/^[a-z0-9:[\]()/_.,%\-&>+~*#'=$!?{}|^]+$/.test(token)) continue;
        found.add(token);
      }
    }
  }
  return found;
}

function sourceFiles(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
      if (SKIP.some((skip) => path.relative(ROOT, full) === skip)) continue;
      sourceFiles(full, out);
    } else if (/\.tsx?$/.test(entry.name)) {
      out.push(full);
    }
  }
  return out;
}

const candidates = new Map(); // class -> the files that name it
for (const dir of SOURCE_DIRS) {
  const full = path.join(ROOT, dir);
  if (!fs.existsSync(full)) continue;
  for (const file of sourceFiles(full)) {
    const source = fs.readFileSync(file, "utf8");
    for (const name of classNamesIn(source)) {
      if (!candidates.has(name)) candidates.set(name, new Set());
      candidates.get(name).add(path.relative(ROOT, file));
    }
  }
}

const entry = fs.readFileSync(path.join(ROOT, "app/tailwind.css"), "utf8");
const compiled = await compile(entry, {
  base: path.join(ROOT, "app"),
  loadStylesheet: async (id) => {
    const resolved = require.resolve(id);
    return {
      base: path.dirname(resolved),
      path: resolved,
      content: fs.readFileSync(resolved, "utf8"),
    };
  },
});

const names = [...candidates.keys()];
const css = compiled.build(names);

// A class that produced a rule appears in the output, escaped the way CSS needs.
const escape = (name) => name.replace(/[.:[\]()/%,#'=$!?{}|^&>+~*]/g, (ch) => "\\" + ch);
const produced = (name) => css.includes("." + escape(name));

// Words that look like classes and are not: they never had a rule to produce, and
// the guard would report every one of them on every run. Kept short deliberately.
const NOT_A_CLASS =
  /^(true|false|null|undefined|button|div|span|img|svg|use|href|src|alt|type|role|id|key|name|value|title|width|height|http|https|utf-8|application\/json|text\/plain|get|post|put|patch|delete|assistant|user|and|or|the|a|an|is|to|of|in|on|for|with|by|at|as|it|be|are|was|were|this|that|from|not|no|yes|one|two|all|any|new|old|off|up|down|left|right|start|end|center|top|bottom|none|auto|both|never|always|polite|assertive|dialog|alert|status|main|nav|header|footer|section|article|aside|form|input|label|select|option|table|thead|tbody|tr|th|td|ul|ol|li|p|h1|h2|h3|h4|h5|h6|a11y|aria|data|dark|light|system|en|ar|he|ur|hi|bn|es|fr|de)$/;

// The hand-written classes globals.css actually defines. Read rather than guessed at
// by shape: "is it kebab-case" would exempt `inset-inline-end-3`, which is precisely
// the invented-utility mistake this guard exists to catch. A name is legacy only if
// there is a rule for it in the stylesheet.
const legacy = new Set();
for (const [, selector] of fs
  .readFileSync(path.join(ROOT, "app/globals.css"), "utf8")
  .matchAll(/\.([a-zA-Z][\w-]*)/g)) {
  legacy.add(selector);
}

const missing = [];
for (const name of names) {
  if (NOT_A_CLASS.test(name)) continue;
  // Only things shaped like a utility: a dash, a variant colon, or a bracketed
  // arbitrary value. A bare word is prose far more often than it is a class.
  if (!/[-:[]/.test(name)) continue;
  if (legacy.has(name)) continue;
  if (!produced(name)) missing.push(name);
}

if (missing.length) {
  console.error(
    `FAIL: ${missing.length} class name(s) produce no CSS. Either the utility does ` +
      `not exist, or its token is missing from app/tailwind.css:`,
  );
  for (const name of missing.sort()) {
    console.error(`  ${name}  (in ${[...candidates.get(name)].sort().join(", ")})`);
  }
  process.exit(1);
}

console.log(`ok: every Tailwind class produces CSS, ${names.length} candidate(s) checked`);
