import { Suspense } from "react";
import { getPortalSession } from "@/lib/supabase/server";
import { getMe } from "@/lib/api/me";
import { getDashboardSummary } from "@/lib/api/portal";
import { PortalDashboardContent } from "@/components/portal-dashboard";
import DashboardLoading from "./loading";

async function DashboardDataFetcher() {
  const session = await getPortalSession();
  const user = session?.user;

  const accessToken = session?.access_token;
  const name =
    typeof user?.user_metadata?.full_name === "string" ? user.user_metadata.full_name : null;

  const [me, summary] = await Promise.all([
    accessToken ? getMe(accessToken) : null,
    accessToken ? getDashboardSummary(accessToken) : null,
  ]);

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

export default function PortalDashboardPage() {
  return (
    <Suspense fallback={<DashboardLoading />}>
      <DashboardDataFetcher />
    </Suspense>
  );
}
