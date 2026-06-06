import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/settings/")({
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <section className="rounded-lg border p-4">
        <h2 className="font-semibold">Beginner mode</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Show plain-language labels and hide advanced metrics by default.
        </p>
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input type="checkbox" className="rounded" />
          Enable beginner mode
        </label>
      </section>
      <section className="rounded-lg border p-4">
        <h2 className="font-semibold">API keys</h2>
        <p className="mt-1 text-sm text-muted-foreground">[Stage 4] Manage subscriber keys.</p>
      </section>
    </div>
  );
}
