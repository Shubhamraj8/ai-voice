import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { isInternalPath, isPortalPath, isPublicPath } from "@/lib/auth/paths";

export type AppHostKind = "local" | "marketing" | "portal" | "internal";

const PORTAL_DEFAULT_PATH = "/portal/dashboard";
const INTERNAL_DEFAULT_PATH = "/internal/tenants";

function hostnameWithoutPort(request: NextRequest): string {
  return (request.headers.get("host") ?? "").split(":")[0].toLowerCase();
}

export function getAppHostKind(hostname: string): AppHostKind {
  if (!hostname || hostname === "localhost" || hostname === "127.0.0.1") {
    return "local";
  }

  if (hostname.startsWith("app.")) {
    return "portal";
  }

  if (hostname.startsWith("internal.")) {
    return "internal";
  }

  return "marketing";
}

function portalHostFromEnv(): string | null {
  const value = process.env.NEXT_PUBLIC_PORTAL_HOST?.trim();
  return value || null;
}

/**
 * Map production subdomains to route groups (design.md § frontend architecture).
 * - app.example.com → /portal/*
 * - internal.example.com → /internal/*
 * - apex / www → marketing; optional redirect of /portal to app subdomain
 */
export function applyHostRouting(request: NextRequest): NextResponse | null {
  const hostname = hostnameWithoutPort(request);
  const kind = getAppHostKind(hostname);
  const { pathname } = request.nextUrl;

  if (kind === "local") {
    return null;
  }

  if (kind === "portal") {
    if (isPublicPath(pathname) || isPortalPath(pathname)) {
      return null;
    }

    if (pathname === "/") {
      return NextResponse.rewrite(new URL(PORTAL_DEFAULT_PATH, request.url));
    }

    return NextResponse.rewrite(new URL(`/portal${pathname}`, request.url));
  }

  if (kind === "internal") {
    if (isPublicPath(pathname) || isInternalPath(pathname)) {
      return null;
    }

    if (pathname === "/") {
      return NextResponse.rewrite(new URL(INTERNAL_DEFAULT_PATH, request.url));
    }

    return NextResponse.rewrite(new URL(`/internal${pathname}`, request.url));
  }

  if (kind === "marketing" && isPortalPath(pathname)) {
    const portalHost = portalHostFromEnv();
    if (portalHost) {
      const target = new URL(pathname, `https://${portalHost}`);
      target.search = request.nextUrl.search;
      return NextResponse.redirect(target);
    }
  }

  return null;
}
