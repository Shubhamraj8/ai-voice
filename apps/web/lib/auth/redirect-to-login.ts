import { redirect } from "next/navigation";
import { sanitizeRedirectPath } from "@/lib/auth/safe-redirect";

/** Server Component guard fallback (middleware runs first). */
export function redirectToLogin(intendedPath: string): never {
  const safe = sanitizeRedirectPath(intendedPath) ?? intendedPath;
  redirect(`/login?redirect=${encodeURIComponent(safe)}`);
}
