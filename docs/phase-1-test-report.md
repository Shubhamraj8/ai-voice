# Phase 1 — Complete Testing Report (ticket 1.19)

End-to-end verification of all Phase 1 deliverables before Phase 2. Executed on a
local Windows dev machine against the live Supabase project (`ap-south-1`) and the
locally-running web (`:3000`) and API (`:8000`) processes.

|        |                                                                                                               |
| ------ | ------------------------------------------------------------------------------------------------------------- |
| Ticket | 1.19 — Phase 1 complete testing                                                                               |
| Date   | 2026-06-02                                                                                                    |
| Branch | `feature/1.19-phase1-testing`                                                                                 |
| Result | **PASS** — all automated suites green; 3 issues found and fixed; 3 items deferred (external / owner decision) |

---

## 1. Test matrix

| #   | Area (ticket)                                     | How tested                                                      | Result                               |
| --- | ------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------ |
| 1   | Migrations applied (1.03)                         | `pnpm --filter @ai-voice/db run migrate:status`                 | ✅ 001–007 applied                   |
| 2   | Cross-tenant RLS isolation (1.04/1.05)            | `pnpm test:rls` (live Supabase, real JWT)                       | ✅ 3/3 pass (after fix — see §2.1)   |
| 3   | Signup auto-provisions tenant (1.09)              | `pnpm --filter @ai-voice/db run test:signup-tenant`             | ✅ pass                              |
| 4   | API JWT auth / `/me` / internal guard (1.11–1.13) | `pytest apps/api/tests`                                         | ✅ 9 pass, 1 skipped                 |
| 5   | Service-role client reads (1.13)                  | `RUN_LIVE_SUPABASE_TESTS=1 pytest tests/test_service_role.py`   | ✅ pass (live)                       |
| 6   | `/health` (1.12)                                  | `curl :8000/health`                                             | ✅ `{"status":"ok","database":"ok"}` |
| 7   | Route-guard helpers (1.08)                        | `pnpm --filter @ai-voice/web run test:guards`                   | ✅ 4/4 pass                          |
| 8   | Route guards live (1.08)                          | `curl` matrix vs running `:3000`                                | ✅ see §3                            |
| 9   | Lint (1.02)                                       | `pnpm lint` (web + api)                                         | ✅ clean                             |
| 10  | Typecheck (1.01/1.02)                             | `pnpm typecheck` (web + shared)                                 | ✅ clean                             |
| 11  | Format (1.02)                                     | `pnpm format:check` (web + api)                                 | ✅ clean (after fix — see §2.2)      |
| 12  | Env var requirements (1.17/1.18)                  | Code-read audit vs `render.yaml` / `.env.example` / deploy docs | ✅ complete (after fix — see §2.3)   |

### Route-guard live results (§3)

| Path                                                  | Expected                         | Observed                                     |
| ----------------------------------------------------- | -------------------------------- | -------------------------------------------- |
| `/`, `/login`, `/signup`                              | 200                              | ✅ 200                                       |
| `/portal`, `/portal/dashboard`, `/portal/calls`       | 307 → `/login?redirect=<path>`   | ✅ redirect with URL-encoded path            |
| `/internal`, `/internal/tenants`, `/internal/metrics` | 307 → `/login?redirect=<path>`   | ✅                                           |
| `/random` (ungrouped)                                 | 307 → `/login` (deny-by-default) | ✅                                           |
| `/auth/callback` (no code)                            | graceful redirect, not 500       | ✅ 307 → `/login?error=auth_callback_failed` |
| `/auth/signout` (POST)                                | session cleared → `/login`       | ✅ 302 → `/login`                            |

---

## 2. Issues found and fixed

### 2.1 — RLS smoke test broke against the 1.09 signup trigger (P1, FIXED)

**Symptom:** `test_rls_select_isolation` failed — tenant A's user saw **two** tenants
where the test asserted exactly one.

**Root cause (not an RLS failure):** The RLS test (ticket 1.05) was written before the
signup trigger (ticket 1.09). `handle_new_user()` in migration `007` auto-provisions a
tenant + `owner` membership for **every** new `auth.users` row. When the test creates its
users via the admin API, each one silently gets an extra tenant. RLS is working perfectly —
user A only ever sees tenants they belong to — but the test's exact-equality assertion
(`tenant_ids == {tenant_a_id}`) no longer held. The teardown also never deleted these
auto-provisioned tenants, leaking orphan rows on every run.

**Fix** (`packages/db/tests/test_rls_isolation.py`):

- Capture each user's auto-provisioned tenant id right after creation (`_auto_tenant_id`).
- Rewrote the isolation assertion to test the actual property: user A sees their own
  tenant, never tenant B's (or B's auto-provisioned tenant).
- Teardown now deletes auth users first (cascading all `tenant_users`), then removes both
  the explicit and the auto-provisioned tenants — no more orphan accumulation.

### 2.2 — `format:check` fails on Windows (CRLF) — breaks `validate` + pre-commit (P2, FIXED)

**Symptom:** `pnpm format:check` reported 90 files with style issues on a Windows checkout.

**Root cause:** No `.gitattributes` + `core.autocrlf=true` means the working tree is CRLF
while git stores LF. Prettier defaults to `endOfLine: "lf"` and flags every CRLF file.
Confirmed line-endings-only: `prettier --check . --end-of-line auto` reports "All matched
files use Prettier code style!". Linux CI (LF) is unaffected, but every Windows contributor
hits a red `pnpm validate` and a failing Husky pre-commit hook.

**Fix** (no reformatting of the 90 files):

- Added [`.gitattributes`](../.gitattributes) — `* text=auto eol=lf` so LF is the canonical
  stored and checked-out form on every platform; binary assets marked `binary`.
- Set `"endOfLine": "auto"` in [`.prettierrc.json`](../.prettierrc.json) so the check
  tolerates existing CRLF working trees. `pnpm validate` now exits 0.

### 2.3 — `NEXT_PUBLIC_SITE_URL` undocumented (P3, FIXED)

**Symptom:** `apps/web/components/landing-page/seo.ts` reads `NEXT_PUBLIC_SITE_URL` for SEO
`metadataBase` / og:url, but the variable was absent from both `.env.example` files **and**
`docs/deploy-vercel.md`. It falls back to `http://localhost:3000`, so if unset on Vercel,
production social previews and canonical URLs point at localhost.

**Fix:** Documented it in [`apps/web/.env.example`](../apps/web/.env.example) and the env-var
table in [`docs/deploy-vercel.md`](./deploy-vercel.md).

---

## 3. Findings deferred (owner decision / external — fix-or-ticket)

### F1 — `provider_config` drift: migration vs design doc (needs owner decision)

Migration `007` and `test_signup_creates_tenant.py` both set the India English default to
`{"stt":"cartesia","tts":"inworld","llm":"deepseek_native"}`. The design doc (§6) and the
most recent commit ("docs: align planning docs with Deepgram voice stack") use
`{"stt":"deepgram","tts":"deepgram","llm":"deepseek_native"}`.

Not changed here because (a) it's a product decision about the canonical v1 voice stack, and
(b) `007` is already applied — editing an applied migration is risky and won't change the
live DB function without an explicit re-apply/new migration. **Recommendation:** decide the
canonical stack; if Deepgram, add a new migration `008` that `CREATE OR REPLACE`s
`handle_new_user()` with the Deepgram config and update the signup test's expected value.

### F2 — Lighthouse landing-page audit (not run locally)

Lighthouse CLI isn't installed in this environment. Recommend running
`npx lighthouse https://<vercel-url> --only-categories=performance` (or Chrome DevTools)
against the deployed marketing page to confirm the 90+ target.

### F3 — Production-only acceptance criteria (cannot verify locally)

These 1.19 criteria depend on live infrastructure and external monitoring:

- "Verify all environment variables set in **Vercel** and **Render**" — verified the
  _required set_ is complete and documented (§2.3); the actual dashboard values must be
  confirmed by someone with access.
- "Confirm warm-ping has kept Render warm 24h+" and "Production deployments stable for 48h+"
  — require the live Render/cron-job.org dashboards and an elapsed observation window.

---

## 4. Honest testing notes (per CONTRIBUTING.md)

- **Authenticated-session route guards** (tenant user reaches `/portal`; internal user
  reaches `/internal`; tenant user _blocked_ from `/internal`) were **not** exercised
  end-to-end in a browser here — they need a real Supabase session cookie. The underlying
  logic is covered indirectly: `paths.ts` + `safe-redirect` unit tests, the live RLS
  `internal_user_full_access` test, and the API `test_internal` success/forbidden tests.
  Recommend a manual browser pass before declaring the ticket fully closed.
- All DB/API tests run against the **live** Supabase project, not a local DB.
