"use client";

import { usePathname } from "next/navigation";
import { getPortalNavItem } from "./nav";

export function PortalPageHeader() {
  const pathname = usePathname();
  const item = getPortalNavItem(pathname);

  return (
    <div className="min-w-0">
      <div className="mb-1 flex items-center gap-2.5">
        <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
        <span className="font-mono text-xs font-medium text-zerqo-muted">Client portal</span>
      </div>
      <p className="truncate text-base font-semibold tracking-tight text-zerqo-ink">{item.label}</p>
    </div>
  );
}
