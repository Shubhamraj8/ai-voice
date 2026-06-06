/**
 * Validates post-login redirect targets (open-redirect safe).
 */

const PORTAL_PREFIX = "/portal";
const INTERNAL_PREFIX = "/internal";

function isSafeRelativePath(path: string): boolean {
  if (!path.startsWith("/") || path.startsWith("//")) {
    return false;
  }
  if (path.includes("://") || path.includes("\\") || path.includes("@")) {
    return false;
  }
  if (path.startsWith("/login") || path.startsWith("/signup") || path.startsWith("/auth")) {
    return false;
  }
  return true;
}

function sanitizeForPrefix(value: string | null | undefined, prefix: string): string | null {
  if (!value) {
    return null;
  }

  const path = value.trim();
  if (!isSafeRelativePath(path)) {
    return null;
  }

  if (path === prefix || path.startsWith(`${prefix}/`)) {
    return path;
  }

  return null;
}

/** Client login — only /portal destinations allowed. */
export function sanitizeClientRedirectPath(value: string | null | undefined): string | null {
  return sanitizeForPrefix(value, PORTAL_PREFIX);
}

/** Internal login — only /internal destinations allowed (not /internal/login). */
export function sanitizeInternalRedirectPath(value: string | null | undefined): string | null {
  const path = sanitizeForPrefix(value, INTERNAL_PREFIX);
  if (path?.startsWith("/internal/login")) {
    return null;
  }
  return path;
}

/** @deprecated Use sanitizeClientRedirectPath or sanitizeInternalRedirectPath */
export function sanitizeRedirectPath(value: string | null | undefined): string | null {
  return sanitizeClientRedirectPath(value) ?? sanitizeInternalRedirectPath(value);
}

export function defaultClientPostLoginPath(): string {
  return "/portal/dashboard";
}

export function defaultInternalPostLoginPath(): string {
  return "/internal/tenants";
}
