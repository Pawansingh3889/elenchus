"use client";

import { AlertTriangle, Clock, TrendingDown, CheckCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";

export type AlertSeverity = "critical" | "warning" | "info" | "success";

interface AlertBadgeProps {
  severity: AlertSeverity;
  count?: number;
  label?: string;
}

export function AlertBadge({ severity, count, label }: AlertBadgeProps) {
  const configs = {
    critical: {
      icon: <AlertTriangle className="size-3" />,
      className: "bg-warn-fill text-warn-text border-warn-border",
      label: "Critical"
    },
    warning: {
      icon: <Clock className="size-3" />,
      className: "bg-highlight-soft text-highlight border-highlight",
      label: "Warning"
    },
    info: {
      icon: <TrendingDown className="size-3" />,
      className: "bg-accent-soft text-accent-strong border-accent",
      label: "Info"
    },
    success: {
      icon: <CheckCircle className="size-3" />,
      className: "bg-green-soft text-green border-green",
      label: "Success"
    }
  };

  const config = configs[severity];

  return (
    <Badge variant="outline" className={`${config.className} gap-1.5`}>
      {config.icon}
      {label || config.label}
      {count !== undefined && `(${count})`}
    </Badge>
  );
}