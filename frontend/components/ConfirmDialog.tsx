"use client";

import { useEffect, useRef } from "react";

interface Props {
  title: string;
  /** The consequence, and anything else the author should see before deciding. */
  children: React.ReactNode;
  confirmLabel: string;
  cancelLabel: string;
  /** Marks the confirm button as the destructive one. Publishing is not; deleting is. */
  danger?: boolean;
  pending?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * A modal that asks before something that cannot be undone.
 *
 * Not `window.confirm`. A native dialog prefixes the page origin ("localhost:3000
 * says"), which reads as the browser warning about the page rather than as the app
 * asking, and it blocks the whole tab. It also cannot render a consequence and two
 * differently-weighted buttons, which is what these decisions need.
 *
 * Every author-facing confirmation goes through this now, including the question
 * editor's answer-type warning, which was the last `window.confirm` on this side of the
 * app. The two in the runner stay: they are the respondent's own withdrawal and rewind,
 * on a page this work deliberately did not touch.
 *
 * The focus rules are the part worth getting right, because a modal that traps nothing
 * is a modal a keyboard user can tab straight out of and act behind:
 *
 * - focus moves to Cancel on open, never to the confirm button, so a stray Enter on the
 *   keystroke that opened the dialog cannot publish a survey
 * - Escape and a click on the backdrop both cancel
 * - focus returns to whatever opened it, so the page is where it was left
 */
export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  cancelLabel,
  danger = false,
  pending = false,
  onConfirm,
  onCancel,
}: Props) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  const openerRef = useRef<Element | null>(null);

  useEffect(() => {
    openerRef.current = document.activeElement;
    cancelRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      // Only if focus is still inside the dialog being torn down: if the confirm
      // navigated somewhere, whatever is focused there has a better claim to it.
      const opener = openerRef.current;
      if (opener instanceof HTMLElement && document.body.contains(opener)) opener.focus();
    };
  }, [onCancel]);

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        // The backdrop closes on click; without this so does every click inside it.
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="modal-title" id="confirm-dialog-title">
          {title}
        </h2>
        <div className="modal-body">{children}</div>
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onCancel} ref={cancelRef}>
            {cancelLabel}
          </button>
          <button
            className={danger ? "btn btn-danger" : "btn btn-primary"}
            onClick={onConfirm}
            disabled={pending}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
