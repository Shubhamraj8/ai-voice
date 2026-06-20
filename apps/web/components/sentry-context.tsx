"use client";

import { useEffect } from "react";
import { setSentryUserContext } from "@/lib/sentry";

/**
 * Tags the Sentry scope with the current tenant + a hashed user id (ticket 5.16).
 * Renders nothing; mount inside the authenticated portal once `me` is known.
 */
export function SentryContext({
  tenantId,
  userId,
}: {
  tenantId?: string | null;
  userId?: string | null;
}) {
  useEffect(() => {
    setSentryUserContext({ tenantId, userId });
  }, [tenantId, userId]);

  return null;
}
