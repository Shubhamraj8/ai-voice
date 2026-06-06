import type { SupabaseClient } from "@supabase/supabase-js";
import {
  defaultClientPostLoginPath,
  defaultInternalPostLoginPath,
  sanitizeClientRedirectPath,
  sanitizeInternalRedirectPath,
} from "@/lib/auth/safe-redirect";

export type ClientLoginResult = { ok: true; path: string } | { ok: false; reason: "internal_only" };

export type InternalLoginResult =
  | { ok: true; path: string }
  | { ok: false; reason: "not_internal" };

async function membership(supabase: SupabaseClient) {
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { user: null, tenantUser: null, internalUser: null };
  }

  const [{ data: tenantUser }, { data: internalUser }] = await Promise.all([
    supabase.from("tenant_users").select("user_id").eq("user_id", user.id).limit(1).maybeSingle(),
    supabase.from("internal_users").select("user_id").eq("user_id", user.id).maybeSingle(),
  ]);

  return { user, tenantUser, internalUser };
}

/** After /login — client portal only. Internal staff must use /internal/login. */
export async function resolveClientPostLoginPath(
  supabase: SupabaseClient,
  redirectParam: string | null
): Promise<ClientLoginResult> {
  const fromQuery = sanitizeClientRedirectPath(redirectParam);
  if (fromQuery) {
    return { ok: true, path: fromQuery };
  }

  const { tenantUser, internalUser } = await membership(supabase);

  if (internalUser && !tenantUser) {
    return { ok: false, reason: "internal_only" };
  }

  if (tenantUser) {
    return { ok: true, path: defaultClientPostLoginPath() };
  }

  return { ok: true, path: defaultClientPostLoginPath() };
}

/** After /internal/login — internal dashboard only. */
export async function resolveInternalPostLoginPath(
  supabase: SupabaseClient,
  redirectParam: string | null
): Promise<InternalLoginResult> {
  const fromQuery = sanitizeInternalRedirectPath(redirectParam);
  if (fromQuery) {
    return { ok: true, path: fromQuery };
  }

  const { internalUser } = await membership(supabase);

  if (!internalUser) {
    return { ok: false, reason: "not_internal" };
  }

  return { ok: true, path: defaultInternalPostLoginPath() };
}
