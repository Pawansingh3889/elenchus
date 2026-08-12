import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge class names, with later Tailwind utilities beating earlier ones.
 *
 * `clsx` handles the conditionals; `twMerge` resolves the conflicts, so a component
 * with a built-in `p-4` can be given `p-6` at the call site and end up with one padding
 * rather than two fighting. Every vendored primitive below takes `className` for
 * exactly that reason. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
