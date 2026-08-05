import type { RunMessage } from "@/lib/types";

/** The conversation as bubbles, shared by the respondent's runner and the author's
 * results view — the two places a transcript is read.
 *
 * `flat` drops the card chrome for the results panel, which is already inside a card.
 * `children` is where the runner puts its typing indicator and scroll anchor, so the
 * live view can grow without the read-only view carrying anything it does not use. */
export function Transcript({
  messages,
  flat = false,
  children,
}: {
  messages: RunMessage[];
  flat?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className={flat ? "chat-thread chat-thread-flat" : "chat-thread"}>
      {messages.map((message, i) => (
        <div key={`${message.created_at}-${i}`} className={`bubble bubble-${message.role}`}>
          {message.content}
        </div>
      ))}
      {children}
    </div>
  );
}
