/** Route classification for auth guards (ticket 1.08). */

export function isClientLoginPath(pathname: string): boolean {
  return pathname === "/login" || pathname.startsWith("/login/");
}

export function isInternalLoginPath(pathname: string): boolean {
  return pathname === "/internal/login" || pathname.startsWith("/internal/login/");
}

export function isPublicPath(pathname: string): boolean {
  return (
    pathname === "/" ||
    isClientLoginPath(pathname) ||
    pathname.startsWith("/signup") ||
    pathname.startsWith("/auth") ||
    isInternalLoginPath(pathname)
  );
}

export function isPortalPath(pathname: string): boolean {
  return pathname === "/portal" || pathname.startsWith("/portal/");
}

export function isInternalPath(pathname: string): boolean {
  if (isInternalLoginPath(pathname)) {
    return false;
  }
  return pathname === "/internal" || pathname.startsWith("/internal/");
}

export function isGuardedAppPath(pathname: string): boolean {
  return isPortalPath(pathname) || isInternalPath(pathname);
}
