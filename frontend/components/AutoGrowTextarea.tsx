"use client";

import { useLayoutEffect, useRef } from "react";

/**
 * A textarea that wraps to a second line and grows to fit, for the places a single line
 * was never enough.
 *
 * Each of these used to be an `<input>`, which shows one line and hides the rest behind
 * a horizontal scroll nobody thinks to drag. A question long enough to be worth asking
 * ("Is this process/operation fully compliant with all applicable regulations and
 * standards?") slid out of view as it was typed, so the author could not read back their
 * own wording without selecting the field and arrowing through it. The live preview beside
 * it showed the full text, which is how the fault stayed invisible for so long: the words
 * were on screen, just not in the box you were editing.
 *
 * The height is set from `scrollHeight` on every value change rather than in CSS, because
 * no CSS sizes a textarea to its content. Resetting to `auto` first is what makes it
 * shrink again: `scrollHeight` never reports less than the height already applied, so
 * without the reset the box only ever grows and deleting a line leaves a gap.
 *
 * `useLayoutEffect` rather than `useEffect` so the measure-and-set happens before the
 * browser paints. With `useEffect` a fast typist sees the box flick to one line and back.
 */
export function AutoGrowTextarea({
  value,
  onChange,
  onEnter,
  className = "field",
  ...rest
}: {
  value: string;
  onChange: (value: string) => void;
  /** Enter sends and Shift+Enter opens a line. Only for the chat composer, where Enter
   *  is what a respondent expects and a newline is the rarer intent. Left undefined
   *  elsewhere, so Enter does the ordinary textarea thing. */
  onEnter?: () => void;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  "aria-label"?: string;
  "aria-invalid"?: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    // scrollHeight is the content box, but the global border-box sizing means the
    // applied height must also cover the borders, or every box sits 2px short of its
    // own last line. offsetHeight minus clientHeight is exactly the border total.
    el.style.height = `${el.scrollHeight + el.offsetHeight - el.clientHeight}px`;
  }, [value]);

  return (
    <textarea
      {...rest}
      ref={ref}
      className={[className, "autogrow"].filter(Boolean).join(" ")}
      rows={1}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => {
        // Never while composing: CJK input methods use Enter to commit the conversion
        // candidate, and treating that keystroke as "send" submits half-typed kana or
        // pinyin the respondent never meant to say. 229 is the legacy signal older
        // browsers raise for the same state.
        if (e.nativeEvent.isComposing || e.keyCode === 229) return;
        if (onEnter && e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          onEnter();
        }
      }}
    />
  );
}
