import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { buildLoginRedirectUrl } from "@/lib/auth/login-url";
import { isInternalPath, isPortalPath, isPublicPath } from "@/lib/auth/paths";

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

  // Refresh session — must not run any logic between createServerClient and
  // getUser() to avoid stale sessions.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;

  if (isPublicPath(pathname)) {
    return supabaseResponse;
  }

  if (isPortalPath(pathname)) {
    if (!user) {
      return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
    }

    const { data: tenantUser } = await supabase
      .from("tenant_users")
      .select("user_id")
      .eq("user_id", user.id)
      .limit(1)
      .maybeSingle();

    if (!tenantUser) {
      return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
    }

    return supabaseResponse;
  }

  if (isInternalPath(pathname)) {
    if (!user) {
      return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
    }

    const { data: internalUser } = await supabase
      .from("internal_users")
      .select("user_id")
      .eq("user_id", user.id)
      .maybeSingle();

    if (!internalUser) {
      return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
    }

    return supabaseResponse;
  }

  if (!user) {
    return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
  }

  return supabaseResponse;
}
