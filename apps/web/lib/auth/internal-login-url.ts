import type { NextRequest } from "next/server";
import { sanitizeInternalRedirectPath } from "@/lib/auth/safe-redirect";

export function buildInternalLoginRedirectUrl(request: NextRequest, redirectPath: string): URL {
  const url = request.nextUrl.clone();
  url.pathname = "/internal/login";
  url.search = "";

  const safe = sanitizeInternalRedirectPath(redirectPath);
  if (safe) {
    url.searchParams.set("redirect", safe);
  }

  return url;
}
