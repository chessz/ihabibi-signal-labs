import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const chipVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      status: {
        UP: "bg-success/15 text-success",
        DEGRADED: "bg-warning/15 text-foreground",
        DOWN: "bg-destructive/15 text-destructive",
        UNKNOWN: "bg-muted text-muted-foreground",
        healthy: "bg-success/15 text-success",
        degraded: "bg-warning/15 text-foreground",
        outage: "bg-destructive/15 text-destructive",
      },
    },
    defaultVariants: { status: "UNKNOWN" },
  },
);

type Props = VariantProps<typeof chipVariants> & {
  label: string;
  className?: string;
};

export function HealthChip({ status, label, className }: Props) {
  return (
    <span className={cn(chipVariants({ status }), className)} role="status">
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {label}
    </span>
  );
}
