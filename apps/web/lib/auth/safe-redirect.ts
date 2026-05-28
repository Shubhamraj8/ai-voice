/**
 * Validates post-login redirect targets (open-redirect safe).
 * Only same-origin relative paths under /portal or /internal are allowed.
 */

const ALLOWED_PREFIXES = ["/portal", "/internal"] as const;

export function sanitizeRedirectPath(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }

  const path = value.trim();

  if (!path.startsWith("/") || path.startsWith("//")) {
    return null;
  }

  if (path.includes("://") || path.includes("\\") || path.includes("@")) {
    return null;
  }

  if (path.startsWith("/login") || path.startsWith("/signup") || path.startsWith("/auth")) {
    return null;
  }

  const allowed = ALLOWED_PREFIXES.some(
    (prefix) => path === prefix || path.startsWith(`${prefix}/`)
  );

  return allowed ? path : null;
}

export function defaultPostLoginPath(): string {
  return "/portal";
}
