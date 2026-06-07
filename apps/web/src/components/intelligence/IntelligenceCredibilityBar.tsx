import { cn } from "@/lib/utils";

type Props = {
  score: string;
  className?: string;
};

export function IntelligenceCredibilityBar({ score, className }: Props) {
  const value = Math.min(100, Math.max(0, Number(score) * 100));
  const tone =
    value >= 85 ? "bg-confidence-high" : value >= 60 ? "bg-primary/60" : "bg-muted-foreground/40";

  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Credibility</span>
        <span>{Math.round(value)}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full transition-all", tone)} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
