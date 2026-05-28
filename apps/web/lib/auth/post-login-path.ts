import type { SupabaseClient } from "@supabase/supabase-js";
import { defaultPostLoginPath, sanitizeRedirectPath } from "@/lib/auth/safe-redirect";

/**
 * Resolve where to send the user after login.
 * Honors ?redirect= when allowed; otherwise picks /portal or /internal by membership.
 */
export async function resolvePostLoginPath(
  supabase: SupabaseClient,
  redirectParam: string | null
): Promise<string> {
  const fromQuery = sanitizeRedirectPath(redirectParam);
  if (fromQuery) {
    return fromQuery;
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return defaultPostLoginPath();
  }

  const [{ data: tenantUser }, { data: internalUser }] = await Promise.all([
    supabase.from("tenant_users").select("user_id").eq("user_id", user.id).limit(1).maybeSingle(),
    supabase.from("internal_users").select("user_id").eq("user_id", user.id).maybeSingle(),
  ]);

  if (tenantUser) {
    return "/portal";
  }

  if (internalUser) {
    return "/internal";
  }

  return defaultPostLoginPath();
}
