import { createFileRoute, Outlet } from "@tanstack/react-router";

import { AppShell } from "@/components/layout/AppShell";

export const Route = createFileRoute("/app")({
  component: AppLayout,
});

function AppLayout() {
  // TODO [Stage 3]: Supabase auth guard — redirect to /login if unauthenticated
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}
