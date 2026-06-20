import type { ErrorEvent } from "@sentry/nextjs";
import { redactText, redactValue } from "./pii-scrub";

// Request headers that must never reach Sentry.
const SENSITIVE_HEADERS = ["authorization", "cookie", "set-cookie", "x-api-key", "apikey"];

/**
 * beforeSend scrubber (tickets 5.16, 5.18): strips cookies, auth headers,
 * query-string secrets, and raw user PII, then runs the shared PII pipeline
 * (lib/pii-scrub) over the debuggable parts of the event so phones, emails,
 * Aadhaar/PAN ids, and cards are replaced with placeholder tokens.
 */
export function scrubEvent(event: ErrorEvent): ErrorEvent | null {
  if (event.request) {
    delete event.request.cookies;

    const headers = event.request.headers;
    if (headers) {
      for (const key of Object.keys(headers)) {
        if (SENSITIVE_HEADERS.includes(key.toLowerCase())) {
          delete headers[key];
        }
      }
    }

    if (
      typeof event.request.query_string === "string" &&
      /token|key|secret|password/i.test(event.request.query_string)
    ) {
      event.request.query_string = "[Filtered]";
    }

    if (event.request.data !== undefined) {
      event.request.data = redactValue(event.request.data);
    }
  }

  if (event.user) {
    delete event.user.email;
    delete event.user.username;
    delete event.user.ip_address;
  }

  // Run the shared PII pipeline over the debuggable payload.
  if (event.message) {
    event.message = redactText(event.message);
  }
  if (event.extra) {
    event.extra = redactValue(event.extra) as typeof event.extra;
  }
  if (event.contexts) {
    event.contexts = redactValue(event.contexts) as typeof event.contexts;
  }
  if (event.breadcrumbs) {
    event.breadcrumbs = redactValue(event.breadcrumbs) as typeof event.breadcrumbs;
  }

  return event;
}
