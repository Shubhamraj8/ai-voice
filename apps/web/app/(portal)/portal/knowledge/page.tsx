import { Suspense } from "react";
import { createClient } from "@/lib/supabase/server";
import { getPortalKnowledge } from "@/lib/api/portal-knowledge";
import { KnowledgeManager } from "@/components/portal-dashboard/knowledge/knowledge-manager";
import KnowledgeLoading from "./loading";

async function KnowledgeDataFetcher() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const accessToken = session?.access_token;
  const docs = accessToken ? await getPortalKnowledge(accessToken) : [];
  return <KnowledgeManager initialDocs={docs} />;
}

export default function PortalKnowledgePage() {
  return (
    <Suspense fallback={<KnowledgeLoading />}>
      <KnowledgeDataFetcher />
    </Suspense>
  );
}
