import { createRootRoute, Link, Outlet } from "@tanstack/react-router";

export const Route = createRootRoute({
  component: () => (
    <>
      <Outlet />
      {import.meta.env.DEV && (
        <footer className="fixed bottom-2 right-2 rounded bg-black/80 px-2 py-1 text-[10px] text-white">
          <Link to="/">dev</Link>
        </footer>
      )}
    </>
  ),
});
