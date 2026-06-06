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

  // Refresh session — must not run any logic between createServerClient and
  // getUser() to avoid stale sessions.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;

  if (isClientLoginPath(pathname)) {
    if (user) {
      const [{ data: tenantUser }, { data: internalUser }] = await Promise.all([
        supabase
          .from("tenant_users")
          .select("user_id")
          .eq("user_id", user.id)
          .limit(1)
          .maybeSingle(),
        supabase.from("internal_users").select("user_id").eq("user_id", user.id).maybeSingle(),
      ]);

      if (internalUser && !tenantUser) {
        const url = request.nextUrl.clone();
        url.pathname = "/internal/login";
        url.search = "";
        return NextResponse.redirect(url);
      }

      if (tenantUser) {
        const url = request.nextUrl.clone();
        url.pathname = "/portal/dashboard";
        url.search = "";
        return NextResponse.redirect(url);
      }
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

    const [{ data: tenantUser }, { data: internalUser }] = await Promise.all([
      supabase.from("tenant_users").select("user_id").eq("user_id", user.id).limit(1).maybeSingle(),
      supabase.from("internal_users").select("user_id").eq("user_id", user.id).maybeSingle(),
    ]);

    if (!tenantUser) {
      if (internalUser) {
        const url = request.nextUrl.clone();
        url.pathname = "/internal/tenants";
        url.search = "";
        return NextResponse.redirect(url);
      }
      return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
    }

    return supabaseResponse;
  }

  if (isInternalPath(pathname)) {
    if (!user) {
      return NextResponse.redirect(buildInternalLoginRedirectUrl(request, pathname));
    }

    const { data: internalUser } = await supabase
      .from("internal_users")
      .select("user_id")
      .eq("user_id", user.id)
      .maybeSingle();

    if (!internalUser) {
      const url = buildInternalLoginRedirectUrl(request, pathname);
      if (user) {
        url.searchParams.set("denied", "1");
      }
      return NextResponse.redirect(url);
    }

    return supabaseResponse;
  }

  if (!user) {
    return NextResponse.redirect(buildLoginRedirectUrl(request, pathname));
  }

  return supabaseResponse;
}
