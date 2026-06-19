/** Display helpers shared across the portal (calls, dashboard, billing). */

/**
 * Mask a caller number for display — keeps the country code and last 4 digits,
 * e.g. "+919876543210" -> "+91 XXXXX X3210". The full number stays in the DB
 * for compliance; masking is presentation-only.
 */
export function maskPhone(raw: string | null | undefined): string {
  if (!raw) return "Unknown";
  const digits = raw.replace(/\D/g, "");
  if (digits.length < 4) return raw;
  const last4 = digits.slice(-4);
  const ccLen = Math.max(0, digits.length - 10);
  const cc = ccLen > 0 ? `+${digits.slice(0, ccLen)} ` : "";
  return `${cc}XXXXX X${last4}`;
}

export function formatDuration(secs: number | null | undefined): string {
  if (secs == null) return "—";
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return m === 0 ? `${s}s` : `${m}m ${s}s`;
}

export function formatShortDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}
