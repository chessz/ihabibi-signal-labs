import { Link } from "@tanstack/react-router";

import { NewsTicker } from "@/components/intelligence/NewsTicker";

const navItems = [
  { to: "/app/signals", label: "Signals" },
  { to: "/app/intelligence", label: "Intelligence" },
  { to: "/app/health", label: "Health" },
  { to: "/app/backtests", label: "Backtests" },
  { to: "/app/strategies", label: "Strategies" },
  { to: "/app/settings", label: "Settings" },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="font-semibold">
            signals-lab
          </Link>
          <nav className="flex gap-4 text-sm" aria-label="Main">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="text-muted-foreground hover:text-foreground [&.active]:font-medium [&.active]:text-foreground"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <NewsTicker />
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  );
}

export function MarketingShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link to="/" className="text-lg font-bold">
            signals-lab
          </Link>
          <nav className="flex gap-6 text-sm">
            <Link to="/academy" className="text-muted-foreground hover:text-foreground">
              Academy
            </Link>
            <Link to="/status" className="text-muted-foreground hover:text-foreground">
              Status
            </Link>
            <Link
              to="/app/signals"
              className="rounded-md bg-primary px-3 py-1.5 text-primary-foreground"
            >
              Open app
            </Link>
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}
