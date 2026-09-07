import { Outlet } from "react-router-dom";

import { SiteHeader } from "./SiteHeader";
import { SiteFooter } from "./SiteFooter";

export function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  );
}
