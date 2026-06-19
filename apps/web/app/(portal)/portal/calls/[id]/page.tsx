import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { getCallDetail } from "@/lib/api/portal";
import { CallDetailView } from "@/components/portal-dashboard/calls/call-detail-view";

export default async function PortalCallDetailPage({ params }: { params: { id: string } }) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const call = session?.access_token ? await getCallDetail(session.access_token, params.id) : null;

  if (!call) {
    return (
      <div className="space-y-6">
        <Link
          href="/portal/calls"
          className="text-[13px] font-medium text-zerqo-muted hover:text-zerqo-ink"
        >
          ← Back to calls
        </Link>
        <div className="rounded-2xl border border-zerqo-line bg-white p-10 text-center shadow-sm">
          <p className="text-sm font-medium text-zerqo-ink">Call not found</p>
          <p className="mt-1 text-[13px] text-zerqo-muted">
            This call doesn&rsquo;t exist or isn&rsquo;t part of your workspace.
          </p>
        </div>
      </div>
    );
  }

  return <CallDetailView call={call} />;
}
