import type { ReactNode } from "react";

import { getGlossaryTerm } from "@/content/glossary/terms";

type Props = {
  termId: string;
  children: ReactNode;
};

export function GlossaryTooltip({ termId, children }: Props) {
  const term = getGlossaryTerm(termId);
  if (!term) return <>{children}</>;

  return (
    <span className="group relative cursor-help border-b border-dotted border-muted-foreground/50">
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-0 z-50 mb-2 hidden w-64 rounded-md border bg-white p-2 text-xs shadow-lg group-hover:block group-focus-within:block"
      >
        <strong>{term.term}:</strong> {term.short}
      </span>
    </span>
  );
}
