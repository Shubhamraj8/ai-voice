import * as Sentry from "@sentry/nextjs";

/**
 * Non-reversible short hash (FNV-1a) so we tag events with an anonymized user
 * identifier instead of a raw id/email (ticket 5.16).
 */
export function hashId(id: string): string {
  let hash = 0x811c9dc5;
  for (let i = 0; i < id.length; i++) {
    hash ^= id.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

/** Tag the current Sentry scope with the tenant and a hashed user id. */
export function setSentryUserContext(params: {
  tenantId?: string | null;
  userId?: string | null;
}): void {
  if (params.tenantId) {
    Sentry.setTag("tenant_id", params.tenantId);
  }
  if (params.userId) {
    Sentry.setUser({ id: hashId(params.userId) });
  }
}
