import { cva, type VariantProps } from "class-variance-authority";

import type { ConfidenceBand } from "@/domain/schemas/signal";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold tabular-nums",
  {
    variants: {
      band: {
        LOW: "bg-muted text-muted-foreground",
        MEDIUM: "bg-warning/15 text-foreground",
        HIGH: "bg-confidence-high/15 text-confidence-high",
        EXTREME: "bg-confidence-extreme/15 text-confidence-extreme",
      },
      size: {
        sm: "text-[10px] px-1.5",
        md: "text-xs",
        lg: "text-sm px-3 py-1",
      },
    },
    defaultVariants: { band: "HIGH", size: "md" },
  },
);

type Props = VariantProps<typeof badgeVariants> & {
  band: ConfidenceBand;
  score?: string;
  className?: string;
};

export function ConfidenceBadge({ band, score, size, className }: Props) {
  const label = score ? `${band} (${score})` : band;
  return (
    <span
      className={cn(badgeVariants({ band, size }), className)}
      aria-label={`Confidence: ${label}`}
    >
      {label}
    </span>
  );
}
