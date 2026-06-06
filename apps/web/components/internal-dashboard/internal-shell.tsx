"use client";

import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { InternalPageHeader } from "./internal-page-header";
import { InternalSidebar } from "./internal-sidebar";
import { InternalUserMenu } from "./internal-user-menu";

type InternalShellProps = {
  role: string;
  email: string;
  name: string | null;
  children: React.ReactNode;
};

export function InternalShell({ role, email, name, children }: InternalShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen font-sans antialiased">
      <div className="hidden md:flex md:shrink-0">
        <InternalSidebar role={role} />
      </div>

      {mobileOpen ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 shadow-2xl">
            <InternalSidebar
              role={role}
              onNavigate={() => setMobileOpen(false)}
              className="h-full"
            />
          </div>
        </div>
      ) : null}

      <div className="internal-grain flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-[60px] items-center justify-between gap-4 border-b border-zerqo-line bg-white/90 px-4 backdrop-blur-md md:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Button
              type="button"
              variant="outline"
              size="icon-sm"
              className="shrink-0 border-zerqo-line bg-white md:hidden"
              aria-label={mobileOpen ? "Close menu" : "Open menu"}
              onClick={() => setMobileOpen((value) => !value)}
            >
              {mobileOpen ? <X className="size-4" /> : <Menu className="size-4" />}
            </Button>
            <InternalPageHeader />
          </div>
          <InternalUserMenu email={email} name={name} role={role} />
        </header>

        <main className={cn("flex-1 px-4 py-8 md:px-8 md:py-10")}>
          <div className="mx-auto w-full max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
