import { createClient, getPortalSession } from "@/lib/supabase/server";
import { getMe } from "@/lib/api/me";
import { redirectToLogin } from "@/lib/auth/redirect-to-login";
import { PortalShell } from "@/components/portal-dashboard/portal-shell";
import { SentryContext } from "@/components/sentry-context";

export default async function PortalLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const session = await getPortalSession();

  const user = session?.user;
  if (!user || !session?.access_token) {
    redirectToLogin("/portal");
  }

  const [tenantUserRes, me] = await Promise.all([
    supabase.from("tenant_users").select("role").eq("user_id", user.id).limit(1).maybeSingle(),
    getMe(session.access_token),
  ]);

  const tenantUser = tenantUserRes.data;
  if (!tenantUser && !me) {
    redirectToLogin("/portal");
  }

  const role = me?.role ?? tenantUser?.role ?? "member";
  const name =
    typeof user.user_metadata?.full_name === "string" ? user.user_metadata.full_name : null;

  return (
    <PortalShell
      tenantName={me?.tenant.business_name ?? "Your workspace"}
      role={role}
      email={user.email ?? me?.user.email ?? "user@tenant.local"}
      name={name}
    >
      <SentryContext tenantId={me?.tenant.id} userId={me?.user.id ?? user.id} />
      {children}
    </PortalShell>
  );
}
