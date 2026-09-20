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

  const {
    data: { session },
  } = await supabase.auth.getSession();
  let user = session?.user ?? null;

  // Fast-path: if session token is valid and not expiring in next 30s,
  // skip remote Supabase Auth network call to keep navigation instant (0ms delay).
  if (session?.access_token) {
    try {
      const parts = session.access_token.split(".");
      if (parts.length === 3) {
        const payload = JSON.parse(Buffer.from(parts[1], "base64").toString());
        if (typeof payload.exp === "number" && payload.exp * 1000 <= Date.now() + 30000) {
          // Token is expired or about to expire -> call getUser() to refresh cookies
          const {
            data: { user: refreshedUser },
          } = await supabase.auth.getUser();
          user = refreshedUser;
        }
      }
    } catch {
      const {
        data: { user: refreshedUser },
      } = await supabase.auth.getUser();
      user = refreshedUser;
    }
  } else {
    const {
      data: { user: refreshedUser },
    } = await supabase.auth.getUser();
    user = refreshedUser;
  }

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
