import { Suspense } from "react";
import { AuditLogViewer } from "@/components/internal-dashboard/audit-log-viewer";

export default function InternalAuditLogPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Loading audit log…</p>}>
      <AuditLogViewer />
    </Suspense>
  );
}
