import { createClient } from "@/lib/supabase/server";
import { redirectToLogin } from "@/lib/auth/redirect-to-login";
import { InternalShell } from "@/components/internal-dashboard/internal-shell";

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

  const name =
    typeof user.user_metadata?.full_name === "string" ? user.user_metadata.full_name : null;

  return (
    <InternalShell
      role={internalUser.role}
      email={user.email ?? "internal@zerqo.local"}
      name={name}
    >
      {children}
    </InternalShell>
  );
}
