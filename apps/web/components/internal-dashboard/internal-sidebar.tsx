"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { internalNavItems } from "./nav";
import { InternalWaveMark } from "./wave-mark";

type InternalSidebarProps = {
  role: string;
  onNavigate?: () => void;
  className?: string;
};

export function InternalSidebar({ role, onNavigate, className }: InternalSidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex h-full w-[260px] flex-col border-r border-white/10 bg-zerqo-black text-white",
        className
      )}
    >
      <div className="px-5 py-6">
        <div className="flex items-center gap-3">
          <InternalWaveMark />
          <div className="min-w-0">
            <p className="truncate text-sm font-bold tracking-tight">AI Voice Agent</p>
            <p className="font-mono text-[10px] font-medium tracking-wider text-white/45 uppercase">
              Internal · {role}
            </p>
          </div>
        </div>
      </div>

      <div className="mx-5 h-px bg-white/10" />

      <nav className="flex flex-1 flex-col gap-0.5 px-3 py-5">
        <p className="mb-3 px-3 font-mono text-[11px] font-medium tracking-widest text-white/45 uppercase">
          Platform
        </p>
        {internalNavItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "internal-nav-active text-white"
                  : "text-white/45 hover:bg-white/5 hover:text-white/80"
              )}
            >
              <span
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors",
                  active ? "bg-zerqo-orange text-white" : "bg-white/10 text-white/45"
                )}
              >
                <Icon className="size-4" />
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 px-5 py-4">
        <p className="font-mono text-[11px] text-white/40">ZERQO · Internal</p>
      </div>
    </aside>
  );
}
