import type { NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";
import { applyHostRouting } from "@/lib/auth/host-routing";

export async function middleware(request: NextRequest) {
  const hostResponse = applyHostRouting(request);
  if (hostResponse) {
    return hostResponse;
  }

  return updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except static files and Next.js internals.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
