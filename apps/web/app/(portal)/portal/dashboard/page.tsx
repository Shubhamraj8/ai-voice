import { createClient } from "@/lib/supabase/server";
import { getMe } from "@/lib/api/me";
import { getDashboardSummary } from "@/lib/api/portal";
import { PortalDashboardContent } from "@/components/portal-dashboard";

export default async function PortalDashboardPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const accessToken = session?.access_token;
  const [me, summary] = await Promise.all([
    accessToken ? getMe(accessToken) : null,
    accessToken ? getDashboardSummary(accessToken) : null,
  ]);

  const name =
    typeof user?.user_metadata?.full_name === "string" ? user.user_metadata.full_name : null;
  const displayName = name?.trim() || me?.user.email?.split("@")[0] || "there";
  const businessName = me?.tenant.business_name ?? "Your workspace";

  return (
    <PortalDashboardContent
      summary={summary}
      displayName={displayName}
      businessName={businessName}
    />
  );
}
