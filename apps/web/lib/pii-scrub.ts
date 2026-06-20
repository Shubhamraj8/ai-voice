/**
 * Shared PII scrubbing rules (ticket 5.18) — the TypeScript mirror of the backend
 * `app/observability/pii_scrub.py`. Same rules, same placeholder tokens; both are
 * exercised against `packages/shared/pii-fixtures.json`.
 */

const EMAIL_RE = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
const PAN_RE = /\b[A-Z]{5}[0-9]{4}[A-Z]\b/g;
const AADHAAR_RE = /\b\d{4}\s\d{4}\s\d{4}\b/g;
const CARD_RE = /\b\d(?:[ -]?\d){12,15}\b/g;
const PHONE_RE = /\+?\d[\d\s\-()]{8,}\d/g;

// Our own staff domains are kept so internal users stay debuggable.
const ALLOWED_EMAIL_DOMAINS = new Set(["zerqo.com"]);
const KNOWN_NAMES: string[] = [];

function luhnOk(digits: string): boolean {
  if (digits.length < 13 || digits.length > 16) return false;
  let total = 0;
  for (let i = 0; i < digits.length; i++) {
    let d = Number(digits[digits.length - 1 - i]);
    if (i % 2 === 1) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    total += d;
  }
  return total % 10 === 0;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function redactText(text: string): string {
  if (!text) return text;
  let out = text
    .replace(EMAIL_RE, (m) => {
      const domain = m.split("@")[1]?.toLowerCase() ?? "";
      return ALLOWED_EMAIL_DOMAINS.has(domain) ? m : "[EMAIL]";
    })
    .replace(PAN_RE, "[PAN]")
    .replace(CARD_RE, (m) => (luhnOk(m.replace(/\D/g, "")) ? "[CARD]" : m))
    .replace(AADHAAR_RE, "[AADHAAR]")
    .replace(PHONE_RE, "[PHONE]");
  for (const name of KNOWN_NAMES) {
    out = out.replace(new RegExp(escapeRegExp(name), "gi"), "[NAME]");
  }
  return out;
}

export function redactValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(redactValue);
  }
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value as Record<string, unknown>)) {
      out[key] = redactValue(val);
    }
    return out;
  }
  if (typeof value === "string") {
    return redactText(value);
  }
  return value;
}
