import { createClient } from "@/lib/supabase/server";
import { getMe } from "@/lib/api/me";
import { redirectToLogin } from "@/lib/auth/redirect-to-login";
import { PortalShell } from "@/components/portal-dashboard/portal-shell";
import { SentryContext } from "@/components/sentry-context";

export default async function PortalLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirectToLogin("/portal");
  }

  const { data: tenantUser } = await supabase
    .from("tenant_users")
    .select("role")
    .eq("user_id", user.id)
    .limit(1)
    .maybeSingle();

  if (!tenantUser) {
    redirectToLogin("/portal");
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const me = session?.access_token ? await getMe(session.access_token) : null;

  const name =
    typeof user.user_metadata?.full_name === "string" ? user.user_metadata.full_name : null;

  return (
    <PortalShell
      tenantName={me?.tenant.business_name ?? "Your workspace"}
      role={me?.role ?? tenantUser.role}
      email={user.email ?? me?.user.email ?? "user@tenant.local"}
      name={name}
    >
      <SentryContext tenantId={me?.tenant.id} userId={me?.user.id ?? user.id} />
      {children}
    </PortalShell>
  );
}
