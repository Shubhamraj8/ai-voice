import type { NextRequest } from "next/server";
import { sanitizeRedirectPath } from "@/lib/auth/safe-redirect";

export function buildLoginRedirectUrl(request: NextRequest, redirectPath: string): URL {
  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";

  const safe = sanitizeRedirectPath(redirectPath);
  if (safe) {
    url.searchParams.set("redirect", safe);
  }

  return url;
}
