import { createFileRoute } from "@tanstack/react-router";

import { MarketingShell } from "@/components/layout/AppShell";
import { glossaryTerms } from "@/content/glossary/terms";

export const Route = createFileRoute("/academy/")({
  component: AcademyPage,
});

function AcademyPage() {
  return (
    <MarketingShell>
      <div className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="text-3xl font-bold">Academy</h1>
        <p className="mt-2 text-muted-foreground">
          Learn crypto signals, confidence, and risk — without the jargon wall.
        </p>
        <ul className="mt-8 space-y-4">
          {glossaryTerms.map((term) => (
            <li key={term.id} className="rounded-lg border p-4">
              <h2 className="font-semibold">{term.term}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{term.short}</p>
              <p className="mt-2 text-sm">{term.long}</p>
            </li>
          ))}
        </ul>
      </div>
    </MarketingShell>
  );
}
