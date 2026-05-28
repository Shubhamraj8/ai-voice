import assert from "node:assert/strict";
import test from "node:test";
import { sanitizeRedirectPath, defaultPostLoginPath } from "./safe-redirect.ts";

test("allows portal and internal paths", () => {
  assert.equal(sanitizeRedirectPath("/portal"), "/portal");
  assert.equal(sanitizeRedirectPath("/portal/settings"), "/portal/settings");
  assert.equal(sanitizeRedirectPath("/internal"), "/internal");
});

test("rejects open redirects and auth loops", () => {
  assert.equal(sanitizeRedirectPath("https://evil.com"), null);
  assert.equal(sanitizeRedirectPath("//evil.com"), null);
  assert.equal(sanitizeRedirectPath("/login"), null);
  assert.equal(sanitizeRedirectPath("/signup"), null);
  assert.equal(sanitizeRedirectPath("/"), null);
  assert.equal(sanitizeRedirectPath(null), null);
});

test("default post-login path", () => {
  assert.equal(defaultPostLoginPath(), "/portal");
});
