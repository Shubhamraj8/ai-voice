import { redirect } from "next/navigation";
import { sanitizeClientRedirectPath } from "@/lib/auth/safe-redirect";

/** Server Component guard fallback (middleware runs first). */
export function redirectToLogin(intendedPath: string): never {
  const safe = sanitizeClientRedirectPath(intendedPath) ?? "/portal/dashboard";
  redirect(`/login?redirect=${encodeURIComponent(safe)}`);
}
