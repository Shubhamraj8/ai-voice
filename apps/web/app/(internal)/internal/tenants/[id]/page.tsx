import { Suspense } from "react";
import { TenantDetailView } from "@/components/internal-dashboard/tenant-detail-view";

type TenantDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function TenantDetailPage({ params }: TenantDetailPageProps) {
  const { id } = await params;

  return (
    <Suspense fallback={<p className="text-muted-foreground">Loading tenant…</p>}>
      <TenantDetailView tenantId={id} />
    </Suspense>
  );
}
