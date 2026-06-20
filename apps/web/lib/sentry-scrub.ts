import type { ErrorEvent } from "@sentry/nextjs";

// Request headers that must never reach Sentry.
const SENSITIVE_HEADERS = ["authorization", "cookie", "set-cookie", "x-api-key", "apikey"];

/**
 * beforeSend scrubber (ticket 5.16): strips cookies, auth headers, query-string
 * secrets, and raw user PII (email/username/IP) from every captured event. The
 * only identifier we keep is the hashed user id we set explicitly. The deeper
 * field-level PII pipeline is centralized in 5.18.
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
  }

  if (event.user) {
    delete event.user.email;
    delete event.user.username;
    delete event.user.ip_address;
  }

  return event;
}
