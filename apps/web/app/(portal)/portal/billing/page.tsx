import { createClient } from "@/lib/supabase/server";
import { getMe } from "@/lib/api/me";
import { getBillingEvents, getBillingSummary } from "@/lib/api/portal";
import { BillingView } from "@/components/portal-dashboard/billing/billing-view";

export default async function PortalBillingPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const accessToken = session?.access_token;
  const [me, summary, events] = await Promise.all([
    accessToken ? getMe(accessToken) : null,
    accessToken ? getBillingSummary(accessToken) : null,
    accessToken ? getBillingEvents(accessToken) : [],
  ]);

  const businessName = me?.tenant.business_name ?? "Your workspace";

  return <BillingView summary={summary} events={events} businessName={businessName} />;
}
