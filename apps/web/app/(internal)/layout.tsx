import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { redirectToLogin } from "@/lib/auth/redirect-to-login";
import { SignOutButton } from "@/components/sign-out-button";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navItems = [{ href: "/internal", label: "Dashboard" }];

export default async function InternalLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirectToLogin("/internal");
  }

  const { data: internalUser } = await supabase
    .from("internal_users")
    .select("role")
    .eq("user_id", user.id)
    .maybeSingle();

  if (!internalUser) {
    redirectToLogin("/internal");
  }

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 flex-col border-r bg-sidebar text-sidebar-foreground">
        <div className="border-b border-sidebar-border px-4 py-4">
          <p className="font-semibold">Internal</p>
          <p className="text-xs text-muted-foreground capitalize">{internalUser.role}</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "justify-start")}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-end border-b px-6">
          <SignOutButton />
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
