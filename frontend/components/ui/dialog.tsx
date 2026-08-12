"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

/* Radix rather than a hand-rolled modal because the parts that are easy to get wrong
   are the parts nobody sees: focus trapping, restoring focus to the trigger on close,
   inert background content, and Escape. The app had three confirmation idioms before
   this, one of which was window.confirm. */

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export function DialogOverlay({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  return (
    <DialogPrimitive.Overlay
      // No enter/leave animation: animate-in and animate-out belong to
      // tailwindcss-animate, which is not installed, so naming them here would style
      // nothing. The overlay appears at once, which is what globals.css does for
      // prefers-reduced-motion readers in any case.
      className={cn("fixed inset-0 z-50 bg-slab/45 backdrop-blur-[1px]", className)}
      {...props}
    />
  );
}

export function DialogContent({
  className,
  children,
  showClose = true,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content> & { showClose?: boolean }) {
  return (
    <DialogPrimitive.Portal>
      <DialogOverlay />
      <DialogPrimitive.Content
        className={cn(
          // start-0/end-0 rather than inset-x-0: they are the logical pair, so the
          // dialog centres the same way in Arabic and Hebrew.
          "fixed z-50 start-0 end-0 mx-auto top-1/2 -translate-y-1/2",
          "w-[min(34rem,calc(100%-2rem))] max-h-[85vh] overflow-y-auto",
          "bg-raised text-ink border border-line rounded-lg shadow-[var(--shadow-md)] p-5",
          className,
        )}
        {...props}
      >
        {children}
        {showClose ? (
          <DialogPrimitive.Close
            className={cn(
              "absolute top-3 end-3 rounded-md p-1 text-muted",
              "hover:text-ink focus-visible:outline-2 focus-visible:outline-focus",
            )}
          >
            <X aria-hidden />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>
        ) : null}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

export function DialogHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex flex-col gap-1 text-start mb-3", className)} {...props} />;
}

export function DialogFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div className={cn("flex flex-wrap justify-end gap-2 mt-5", className)} {...props} />
  );
}

export function DialogTitle({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title className={cn("text-lg font-semibold", className)} {...props} />
  );
}

export function DialogDescription({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description className={cn("text-sm text-muted", className)} {...props} />
  );
}
