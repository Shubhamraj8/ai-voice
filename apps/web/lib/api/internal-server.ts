import { createClient } from "@/lib/supabase/server";
import { getApiBaseUrl } from "./config";

/** Promote founding internal user via API, then re-check membership. */
export async function resolveInternalUserRole(): Promise<string | null> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    return null;
  }

  const { data: existing } = await supabase
    .from("internal_users")
    .select("role")
    .eq("user_id", session.user.id)
    .maybeSingle();

  if (existing?.role) {
    return existing.role;
  }

  await fetch(`${getApiBaseUrl()}/internal/ping`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
    cache: "no-store",
  }).catch(() => null);

  const { data: promoted } = await supabase
    .from("internal_users")
    .select("role")
    .eq("user_id", session.user.id)
    .maybeSingle();

  return promoted?.role ?? null;
}
