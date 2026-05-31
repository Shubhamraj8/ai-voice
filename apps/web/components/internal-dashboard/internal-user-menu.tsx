"use client";

import { ChevronDown, LogOut } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type InternalUserMenuProps = {
  email: string;
  name: string | null;
  role: string;
};

function initialsFrom(name: string, email: string) {
  const source = name.trim() || email.split("@")[0];
  const parts = source.split(/[\s._-]+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return source.slice(0, 2).toUpperCase();
}

export function InternalUserMenu({ email, name, role }: InternalUserMenuProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const displayName = name?.trim() || email.split("@")[0];

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative shrink-0">
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
        className={cn(
          buttonVariants({ variant: "outline", size: "sm" }),
          "h-9 gap-2 border-zerqo-line bg-white pl-1.5 shadow-sm hover:bg-zerqo-cream"
        )}
      >
        <Avatar size="sm" className="size-7">
          <AvatarFallback className="bg-zerqo-ink text-xs font-semibold text-white">
            {initialsFrom(displayName, email)}
          </AvatarFallback>
        </Avatar>
        <span className="hidden max-w-[120px] truncate text-zerqo-ink sm:inline">
          {displayName}
        </span>
        <ChevronDown
          className={cn("size-4 text-zerqo-faint transition-transform", open && "rotate-180")}
        />
      </button>

      {open ? (
        <div
          role="menu"
          aria-label="Account menu"
          className="absolute right-0 top-[calc(100%+6px)] z-[100] w-60 overflow-hidden rounded-xl border border-zerqo-line bg-white p-1 shadow-lg ring-1 ring-black/5"
        >
          <div className="px-3 py-2.5">
            <p className="truncate text-sm font-semibold text-zerqo-ink">{displayName}</p>
            <p className="truncate text-xs text-zerqo-muted">{email}</p>
            <p className="mt-1 font-mono text-[11px] capitalize text-zerqo-orange">
              {role} · internal
            </p>
          </div>

          <div className="my-1 h-px bg-zerqo-line" />

          <form action="/auth/signout" method="POST">
            <button
              type="submit"
              role="menuitem"
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-zerqo-ink transition-colors hover:bg-zerqo-cream"
            >
              <LogOut className="size-4 text-zerqo-muted" />
              Sign out
            </button>
          </form>
        </div>
      ) : null}
    </div>
  );
}
