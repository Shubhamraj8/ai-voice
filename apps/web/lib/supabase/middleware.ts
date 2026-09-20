import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { buildInternalLoginRedirectUrl } from "@/lib/auth/internal-login-url";
import { buildLoginRedirectUrl } from "@/lib/auth/login-url";
import {
  isClientLoginPath,
  isInternalLoginPath,
  isInternalPath,
  isPortalPath,
  isPublicPath,
} from "@/lib/auth/paths";

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // IMPORTANT: Must use getUser() (not getSession()) here so that Supabase
  // refreshes expired tokens and writes fresh cookies back to the response.
  // getSession() only reads cookies without validating/refreshing the token,
  // which causes downstream API calls to fail with stale access tokens.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;

  if (isClientLoginPath(pathname)) {
    if (user) {
      const url = request.nextUrl.clone();
      url.pathname = "/portal/dashboard";
      url.search = "";
      return NextResponse.redirect(url);
    }

    return supabaseResponse;
  }

  if (isInternalLoginPath(pathname)) {
    return supabaseResponse;
  }

  if (isPublicPath(pathname)) {
    return supabaseResponse;
  }

  if (isPortalPath(pathname)) {
    if (!user) {
      return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
    }
    return supabaseResponse;
  }

  if (isInternalPath(pathname)) {
    if (!user) {
      return NextResponse.redirect(buildInternalLoginRedirectUrl(request, pathname));
    }
    return supabaseResponse;
  }

  if (!user) {
    return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
  }

  return supabaseResponse;
}
