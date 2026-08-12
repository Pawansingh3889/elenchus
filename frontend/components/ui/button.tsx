"use client";

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

/* Vendored from shadcn/ui and adapted in two ways, both deliberate:
   - Every physical utility is logical (ps-/pe-, ms-/me-, text-start), because this app
     ships in Arabic, Hebrew and Urdu and check_logical_properties.py holds the CSS to
     the same rule.
   - The variants name this app's palette rather than shadcn's defaults, so `primary`
     is the dark slab the top bar already uses and `ai` is the one affordance that
     spends a model call, which has always looked different here on purpose.
   `--tap` is 44px, the smallest reliably hittable control on a phone; the min-height
   below is that token rather than a number so a change lands everywhere at once. */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium " +
    "whitespace-nowrap transition-colors cursor-pointer " +
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus " +
    "disabled:pointer-events-none disabled:opacity-55 " +
    "[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-slab text-on-slab hover:opacity-90",
        secondary: "bg-raised text-ink border border-line hover:bg-surface",
        ai: "bg-ai-fill text-accent-strong border border-ai-border hover:bg-highlight-soft",
        danger: "bg-err-fill text-err-text border border-err-border hover:opacity-90",
        quiet: "bg-transparent text-muted hover:text-ink hover:bg-surface",
        link: "bg-transparent text-accent-strong underline-offset-4 hover:underline",
      },
      size: {
        sm: "min-h-8 px-3 text-xs",
        md: "min-h-[var(--tap)] px-4",
        icon: "size-[var(--tap)] p-0",
      },
    },
    defaultVariants: { variant: "secondary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Render as the child element instead of a button, for links that look like buttons. */
  asChild?: boolean;
}

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}

export { buttonVariants };
