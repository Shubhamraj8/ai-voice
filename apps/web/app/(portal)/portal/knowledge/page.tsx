import { createClient } from "@/lib/supabase/server";
import { getPortalKnowledge } from "@/lib/api/portal-knowledge";
import { KnowledgeManager } from "@/components/portal-dashboard/knowledge/knowledge-manager";

export default async function PortalKnowledgePage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const docs = session?.access_token ? await getPortalKnowledge(session.access_token) : [];

  return <KnowledgeManager initialDocs={docs} />;
}
