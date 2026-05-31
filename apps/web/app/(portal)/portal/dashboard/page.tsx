import { createClient } from "@/lib/supabase/server";
import { getMe } from "@/lib/api/me";
import { PortalDashboardContent } from "@/components/portal-dashboard";

export default async function PortalDashboardPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const me = session?.access_token ? await getMe(session.access_token) : null;
  const name =
    typeof user?.user_metadata?.full_name === "string" ? user.user_metadata.full_name : null;

  return <PortalDashboardContent me={me} fallbackName={name} />;
}
