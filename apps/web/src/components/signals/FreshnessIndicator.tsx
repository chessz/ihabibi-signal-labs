import { Clock } from "lucide-react";

import { cn, formatAge } from "@/lib/utils";

type FreshnessLevel = "fresh" | "stale" | "unknown";

function levelFromAge(seconds: number | undefined): FreshnessLevel {
  if (seconds === undefined) return "unknown";
  if (seconds <= 120) return "fresh";
  if (seconds <= 600) return "stale";
  return "stale";
}

const levelStyles: Record<FreshnessLevel, string> = {
  fresh: "text-success",
  stale: "text-warning",
  unknown: "text-muted-foreground",
};

type Props = {
  ageSeconds?: number;
  label?: string;
  className?: string;
};

export function FreshnessIndicator({ ageSeconds, label = "Updated", className }: Props) {
  const level = levelFromAge(ageSeconds);
  const text =
    ageSeconds !== undefined ? `${label} ${formatAge(ageSeconds)}` : `${label}: unknown`;

  return (
    <span
      className={cn("inline-flex items-center gap-1 text-xs", levelStyles[level], className)}
      role="status"
      aria-live="polite"
    >
      <Clock className="h-3 w-3" aria-hidden />
      {text}
    </span>
  );
}
