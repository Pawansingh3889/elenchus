"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  Area,
  AreaChart,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { Card } from "@/components/ui/card";

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    period: string;
  };
  miniChart?: {
    data: Array<{ name: string; value: number }>;
    type?: "area" | "line";
  };
  color?: "accent" | "warn" | "highlight" | "muted";
}

export function KpiCard({
  title,
  value,
  subtitle,
  trend,
  miniChart,
  color = "accent",
}: KpiCardProps) {
  const colorClasses = {
    accent: "text-accent-strong",
    warn: "text-warn-text",
    highlight: "text-highlight",
    muted: "text-muted",
  };

  const trendIcon = trend ? (
    trend.value > 0 ? (
      <TrendingUp className="size-4 text-accent-strong" />
    ) : trend.value < 0 ? (
      <TrendingDown className="size-4 text-warn-text" />
    ) : (
      <Minus className="size-4 text-muted" />
    )
  ) : null;

  const trendText = trend ? (
    <span className={`text-sm ${trend.value > 0 ? "text-accent-strong" : trend.value < 0 ? "text-warn-text" : "text-muted"}`}>
      {trend.value > 0 ? "+" : ""}{trend.value}% {trend.period}
    </span>
  ) : null;

  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <h3 className="text-sm font-medium text-muted">{title}</h3>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-semibold ${colorClasses[color]}`}>
              {value}
            </span>
            {trendText}
          </div>
          {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
        </div>
        {trendIcon}
      </div>

      {miniChart && miniChart.data.length > 0 && (
        <div className="h-16 w-full">
          <ResponsiveContainer width="100%" height="100%">
            {miniChart.type === "line" ? (
              <LineChart data={miniChart.data}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="currentColor"
                  strokeWidth={2}
                  dot={false}
                  className={colorClasses[color]}
                />
                <Tooltip />
              </LineChart>
            ) : (
              <AreaChart data={miniChart.data}>
                <defs>
                  <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="currentColor" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="currentColor" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="currentColor"
                  strokeWidth={2}
                  fill={`url(#gradient-${color})`}
                  className={colorClasses[color]}
                />
                <Tooltip />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}