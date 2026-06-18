import { Suspense } from "react";
import { LeadsInbox } from "@/components/internal-dashboard/leads-inbox";

export default function InternalLeadsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Loading leads…</p>}>
      <LeadsInbox />
    </Suspense>
  );
}
