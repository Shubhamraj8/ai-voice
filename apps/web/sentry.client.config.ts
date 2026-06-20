import * as Sentry from "@sentry/nextjs";
import { scrubEvent } from "./lib/sentry-scrub";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

// No-op when no DSN is configured (e.g. local dev) — like the Redis/Resend guards.
Sentry.init({
  dsn,
  enabled: Boolean(dsn),
  // 100% of errors, 10% of performance traces (ticket 5.16).
  sampleRate: 1.0,
  tracesSampleRate: 0.1,
  sendDefaultPii: false,
  release: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA,
  environment: process.env.NEXT_PUBLIC_VERCEL_ENV ?? process.env.NODE_ENV,
  beforeSend: scrubEvent,
});
