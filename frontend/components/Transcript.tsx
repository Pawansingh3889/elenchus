import type { RunMessage, RunMessageDetail } from "@/lib/types";

/** What produced this line, for the author reading a transcript back.
 *
 *  Rendered only where all of it is known. A half-stamp ("conduct_v7" with no model) is
 *  the shape a failed turn leaves behind, and showing it beside a message that was in
 *  fact delivered would read as the record of a turn that happened rather than the gap
 *  it is. The respondent's own words and the engine's opening line carry nothing, and
 *  get nothing. */
function provenance(message: RunMessage | RunMessageDetail): string | null {
  const { prompt_version: prompt, model, tier } = message as RunMessageDetail;
  if (!prompt || !model) return null;
  return tier == null ? `${prompt} · ${model}` : `${prompt} · ${model} (tier ${tier})`;
}

/** The conversation as bubbles, shared by the respondent's runner and the author's
 * results view — the two places a transcript is read.
 *
 * `flat` drops the card chrome for the results panel, which is already inside a card.
 * `children` is where the runner puts its typing indicator and scroll anchor, so the
 * live view can grow without the read-only view carrying anything it does not use.
 *
 * The message type is the union on purpose: the runner passes RunMessage, which never
 * carries provenance, and the results view passes RunMessageDetail, which does. One
 * component either way, because the bubbles are the same bubbles. */
export function Transcript({
  messages,
  flat = false,
  children,
}: {
  messages: (RunMessage | RunMessageDetail)[];
  flat?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className={flat ? "chat-thread chat-thread-flat" : "chat-thread"}>
      {messages.map((message, i) => {
        const stamp = provenance(message);
        return (
          <div key={`${message.created_at}-${i}`} className={`bubble bubble-${message.role}`}>
            {message.content}
            {stamp ? <span className="bubble-provenance">{stamp}</span> : null}
          </div>
        );
      })}
      {children}
    </div>
  );
}
