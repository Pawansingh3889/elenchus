import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium " +
    "whitespace-nowrap",
  {
    variants: {
      variant: {
        neutral: "bg-surface text-muted border-line",
        accent: "bg-ai-fill text-accent-strong border-ai-border",
        warn: "bg-warn-fill text-warn-text border-warn-border",
        danger: "bg-err-fill text-err-text border-err-border",
        solid: "bg-slab text-on-slab border-transparent",
        outline: "border-line text-ink hover:bg-surface",
      },
    },
    defaultVariants: { variant: "neutral" },
  },
);

export function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { badgeVariants };
