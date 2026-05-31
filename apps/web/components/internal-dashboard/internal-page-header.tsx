"use client";

import { usePathname } from "next/navigation";
import { getInternalNavItem } from "./nav";

export function InternalPageHeader() {
  const pathname = usePathname();
  const item = getInternalNavItem(pathname);

  return (
    <div className="min-w-0">
      <div className="mb-1 flex items-center gap-2.5">
        <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
        <span className="font-mono text-xs font-medium text-zerqo-muted">Internal ops</span>
      </div>
      <p className="truncate text-base font-semibold tracking-tight text-zerqo-ink">{item.label}</p>
    </div>
  );
}
