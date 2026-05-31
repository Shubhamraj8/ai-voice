import assert from "node:assert/strict";
import test from "node:test";
import { getAppHostKind } from "./host-routing.ts";

test("getAppHostKind classifies subdomains", () => {
  assert.equal(getAppHostKind("localhost"), "local");
  assert.equal(getAppHostKind("127.0.0.1"), "local");
  assert.equal(getAppHostKind("yourdomain.ai"), "marketing");
  assert.equal(getAppHostKind("www.yourdomain.ai"), "marketing");
  assert.equal(getAppHostKind("app.yourdomain.ai"), "portal");
  assert.equal(getAppHostKind("internal.yourdomain.ai"), "internal");
  assert.equal(getAppHostKind("ai-voice.vercel.app"), "marketing");
});
