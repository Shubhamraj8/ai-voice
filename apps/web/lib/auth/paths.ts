/** Route classification for auth guards (ticket 1.08). */

export function isPublicPath(pathname: string): boolean {
  return (
    pathname === "/" ||
    pathname.startsWith("/login") ||
    pathname.startsWith("/signup") ||
    pathname.startsWith("/auth")
  );
}

export function isPortalPath(pathname: string): boolean {
  return pathname === "/portal" || pathname.startsWith("/portal/");
}

export function isInternalPath(pathname: string): boolean {
  return pathname === "/internal" || pathname.startsWith("/internal/");
}

export function isGuardedAppPath(pathname: string): boolean {
  return isPortalPath(pathname) || isInternalPath(pathname);
}
