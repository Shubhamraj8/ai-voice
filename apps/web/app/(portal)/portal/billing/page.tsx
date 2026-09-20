import { Suspense } from "react";
import { getPortalSession } from "@/lib/supabase/server";
import { getMe } from "@/lib/api/me";
import { getBillingEvents, getBillingSummary } from "@/lib/api/portal";
import { BillingView } from "@/components/portal-dashboard/billing/billing-view";
import BillingLoading from "./loading";

async function BillingDataFetcher() {
  const session = await getPortalSession();
  const accessToken = session?.access_token;

  const [me, summary, events] = await Promise.all([
    accessToken ? getMe(accessToken) : null,
    accessToken ? getBillingSummary(accessToken) : null,
    accessToken ? getBillingEvents(accessToken) : [],
  ]);

  const businessName = me?.tenant.business_name ?? "Your workspace";

  return <BillingView summary={summary} events={events} businessName={businessName} />;
}

export default function PortalBillingPage() {
  return (
    <Suspense fallback={<BillingLoading />}>
      <BillingDataFetcher />
    </Suspense>
  );
}
