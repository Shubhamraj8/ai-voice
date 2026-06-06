import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { resolveInternalUserRole } from "@/lib/api/internal-server";
import { InternalShell } from "@/components/internal-dashboard/internal-shell";

export default async function InternalLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/internal/login?redirect=/internal");
  }

  const role = await resolveInternalUserRole();

  if (!role) {
    redirect("/internal/login?denied=1");
  }

  const name =
    typeof user.user_metadata?.full_name === "string" ? user.user_metadata.full_name : null;

  return (
    <InternalShell role={role} email={user.email ?? "internal@zerqo.local"} name={name}>
      {children}
    </InternalShell>
  );
}
