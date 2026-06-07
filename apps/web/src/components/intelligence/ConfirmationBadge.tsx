import { cn } from "@/lib/utils";

type Props = {
  count: number;
  className?: string;
};

export function ConfirmationBadge({ count, className }: Props) {
  if (count < 2) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary",
        className,
      )}
    >
      ×{count} sources
    </span>
  );
}
