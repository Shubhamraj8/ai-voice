import { createClient } from "@/lib/supabase/server";
import { getCalls, type CallsQuery } from "@/lib/api/portal";
import { PortalCallsView } from "@/components/portal-dashboard/calls/portal-calls-view";

export default async function PortalCallsPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined };
}) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const get = (key: string) => {
    const value = searchParams[key];
    return typeof value === "string" && value.length > 0 ? value : undefined;
  };

  const query: CallsQuery = {
    page: Number(get("page")) || 1,
    outcome: get("outcome"),
    intent: get("intent"),
    search: get("q"),
    date_from: get("from"),
    date_to: get("to"),
  };

  const data = session?.access_token ? await getCalls(session.access_token, query) : null;

  return <PortalCallsView data={data} query={query} />;
}
