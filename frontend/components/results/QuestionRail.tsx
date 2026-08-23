"use client";

import { useEffect, useState } from "react";

import { useT } from "@/lib/i18n/useT";
import { cn } from "@/lib/utils";

/**
 * The list of questions, always on screen, with the one you are reading marked.
 *
 * Eight questions is eight charts and no way to tell where you are in them or how many
 * are left; twenty would be worse. Every BI tool keeps a field list beside the canvas and
 * every long report keeps a contents rail, for the same two jobs: say what is here, and
 * get me to one of them without scrolling past the rest.
 *
 * It is not a second flag strip. The strip says *why* to look at a question and names
 * the finding; this says *where* everything is and marks the flagged ones so the two
 * agree. Both stay.
 *
 * **Scroll position decides what is current, not clicks.** Clicking sets the scroll, and
 * the scroll sets the highlight, so arriving at a card by any route (the rail, the flag
 * strip, a link somebody sent) lights the same entry. Reading which card is under the
 * bar is one pass over a handful of elements per frame, throttled to one per animation
 * frame; an IntersectionObserver would need its rootMargin baked in at construction, and
 * the offset it would need is the control bar's height, which changes as chips appear.
 *
 * Below lg it is a horizontal row above the cards and does not stick, because two sticky
 * bands on a narrow screen is most of the screen.
 */
export function QuestionRail({
  questions,
}: {
  questions: { id: string; text: string }[];
}) {
  const msg = useT();
  const [current, setCurrent] = useState<string | null>(questions[0]?.id ?? null);

  useEffect(() => {
    if (questions.length === 0) return;
    let frame = 0;
    const read = () => {
      frame = 0;
      // The line the sticky bar clears. Anything above it is behind the bar, so the
      // current card is the last one whose top has passed it.
      const bar =
        parseFloat(
          getComputedStyle(document.documentElement).getPropertyValue("--controls-h"),
        ) || 0;
      const line = bar + 24;
      let found = questions[0].id;
      for (const question of questions) {
        const el = document.getElementById(`question-${question.id}`);
        if (el && el.getBoundingClientRect().top <= line) found = question.id;
      }
      setCurrent(found);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(read);
    };
    read();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [questions]);

  if (questions.length === 0) return null;

  return (
    <nav
      aria-label={msg.results.questionsHeading}
      className={cn(
        // Horizontal and scrollable on a narrow screen, a column that sticks on a wide
        // one. The sticky offset is the bar's own published height, so the rail sits
        // under it whether it is one row or three.
        "flex gap-1 overflow-x-auto pb-1",
        "lg:sticky lg:h-fit lg:w-56 lg:shrink-0 lg:flex-col lg:overflow-visible lg:pb-0",
      )}
      style={{ top: "calc(var(--controls-h, 0px) + 1rem)" }}
    >
      {questions.map((question, i) => (
        <a
          key={question.id}
          href={`#question-${question.id}`}
          aria-current={current === question.id ? "true" : undefined}
          className={cn(
            "flex shrink-0 items-center gap-1.5 rounded-md px-2 py-1 text-sm lg:shrink",
            current === question.id
              ? "bg-ai-fill font-medium text-accent-strong"
              : "text-muted hover:bg-surface",
          )}
        >
          <span className="tabular-nums">{msg.results.railNumber(i + 1)}</span>
          {/* The text, cut to one line. The card below carries it in full; here it is
              only enough to tell one question from another. */}
          <span className="truncate lg:flex-1" title={question.text}>
            {question.text}
          </span>
        </a>
      ))}
    </nav>
  );
}
