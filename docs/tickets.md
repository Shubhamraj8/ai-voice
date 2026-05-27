# Tickets

Development tickets organized by phase. Each ticket follows the naming convention `<phase>.<number>` and includes description, tasks, acceptance criteria, dependencies on other tickets, and an estimate in hours (assuming AI-IDE-assisted coding).

Companion to `mvp-planning.md`, `features.md`, `design.md`, and `roadmap.md`.

---

## Contents

- [Phase 1 — Foundation](#phase-1--foundation)
- [Phase 2 — Voice pipeline](#phase-2--voice-pipeline)

---

# Phase 1 — Foundation

Foundation week. Both apps deployed, auth working, database schema and RLS in place.

---

## 1.01 — Repo bootstrap

**Description**: Set up monorepo structure with apps/web (Next.js) and apps/api (FastAPI), shared packages folder, and base tooling.

**Tasks**:
- Create monorepo with `pnpm` workspaces
- Initialize `/apps/web` with Next.js 14 (App Router, TypeScript)
- Initialize `/apps/api` with FastAPI + Python 3.11 + uv or pip
- Add `/packages/db` and `/packages/shared` folders
- Add root-level `.gitignore`, `.editorconfig`, `README.md`
- Set up `pnpm dev` to run both apps in parallel

**Acceptance criteria**:
- `pnpm install` works from root with no errors
- `pnpm dev` boots Next.js on `:3000` and FastAPI on `:8000` simultaneously
- Both apps return hello-world on their root paths
- TypeScript strict mode enabled in `apps/web`
- Folder structure matches `mvp-planning.md` spec

**Dependencies**: None

**Estimate**: 2h

---

## 1.02 — Tooling and CI

**Description**: Configure linting, formatting, type-checking, and GitHub Actions for both apps.

**Tasks**:
- Configure ESLint + Prettier for `apps/web`
- Configure Ruff + Black for `apps/api`
- Add `tsc --noEmit` typecheck script
- Add pre-commit hook via Husky or pre-commit
- Create GitHub Actions workflow for lint + typecheck on PR
- Add status badges to `README.md`

**Acceptance criteria**:
- Lint passes on a fresh clone
- Typecheck passes on a fresh clone
- Pre-commit hook blocks bad commits locally
- CI runs and passes on a test PR
- Both web and api have separate CI jobs

**Dependencies**: 1.01

**Estimate**: 2h

---

## 1.03 — Supabase project and base schema

**Description**: Provision Supabase project in ap-south-1 and create migrations for core tables.

**Tasks**:
- Create Supabase project in `ap-south-1` region
- Enable pgvector and uuid-ossp extensions
- Write migration for `tenants` table
- Write migration for `tenant_users` and `internal_users` tables
- Write migration for `agents` and `audit_log` tables
- Write migration for `calls` and `call_messages` tables

**Acceptance criteria**:
- All migrations apply cleanly to a fresh DB
- pgvector extension is active
- Foreign keys and indexes match `design.md` §7
- Migration runner can roll back and re-apply
- Schema diff between local and Supabase shows zero drift

**Dependencies**: None

**Estimate**: 3h

---

## 1.04 — RLS policies

**Description**: Add Row Level Security policies to every tenant-scoped table with separate paths for tenant users and internal users.

**Tasks**:
- Enable RLS on `tenants`, `agents`, `calls`, `call_messages`, `audit_log`
- Write tenant-user isolation policy for each table
- Write internal-user full-access policy for each table
- Add helper SQL function `current_tenant_id()` for use in policies
- Document policy patterns in `/packages/db/README.md`

**Acceptance criteria**:
- All tenant-scoped tables have RLS enabled
- Tenant user can read only their own rows in every table
- Internal user can read all rows in every table
- Policies use `auth.uid()` consistently
- Migration applies idempotently

**Dependencies**: 1.03

**Estimate**: 2h

---

## 1.05 — Cross-tenant smoke test

**Description**: Write a SQL or Python test that verifies tenant A cannot read tenant B's data under any code path.

**Tasks**:
- Seed two tenants with one user each in test data
- Insert sample agents and calls for both
- Authenticate as tenant A's user and query all tenant-scoped tables
- Assert zero rows from tenant B leak through
- Repeat for `INSERT`, `UPDATE`, `DELETE` operations
- Add this test to CI

**Acceptance criteria**:
- Test passes on first run
- Test fails if RLS is disabled on any table
- Test runs in under 10 seconds
- Test is wired into CI pipeline
- README explains how to run locally

**Dependencies**: 1.02, 1.04

**Estimate**: 2h

---

## 1.06 — Supabase Auth — frontend wiring

**Description**: Integrate Supabase Auth into the Next.js app with email/password sign-up and sign-in.

**Tasks**:
- Install `@supabase/ssr` and `@supabase/supabase-js`
- Create Supabase client helpers for server and client components
- Build `/login` page with email + password form
- Build `/signup` page with email + password form
- Build `/auth/callback` route handler for email confirmation
- Add `/auth/signout` route

**Acceptance criteria**:
- New user can sign up with email + password
- Email confirmation flow works end-to-end
- User can log in and log out
- Auth cookies set correctly for SSR
- Errors (wrong password, duplicate email) display gracefully

**Dependencies**: 1.01, 1.03

**Estimate**: 3h

---

## 1.07 — Route groups and layouts

**Description**: Set up Next.js route groups for marketing, internal dashboard, and client portal with appropriate layouts.

**Tasks**:
- Create `(marketing)`, `(internal)`, `(portal)` route groups
- Build root layout with Tailwind + shadcn/ui base
- Build marketing layout (no auth required)
- Build internal layout (requires internal-user role)
- Build portal layout (requires tenant-user)
- Install shadcn/ui base components: Button, Card, Input, Form

**Acceptance criteria**:
- Visiting `/` shows marketing layout
- Visiting `/portal` and `/internal` apply correct layouts
- Tailwind classes work across all groups
- shadcn components render with the right theme
- Navigation between groups preserves auth state

**Dependencies**: 1.01

**Estimate**: 3h

---

## 1.08 — Route guards

**Description**: Protect `/portal` and `/internal` routes by redirecting unauthenticated or unauthorized users.

**Tasks**:
- Create middleware that reads Supabase session
- Redirect unauthenticated users from `/portal` to `/login`
- Redirect non-internal users from `/internal` to `/login`
- Allow authenticated tenant users on `/portal`
- Add `?redirect=` query param to return user to original page after login
- Test all four redirect scenarios

**Acceptance criteria**:
- Unauthenticated user on `/portal` redirects to `/login`
- Authenticated tenant user on `/internal` redirects to `/login` (not authorized)
- Authenticated internal user reaches `/internal`
- `?redirect=` param works correctly after login
- No flash of unauthorized content (SSR-guarded)

**Dependencies**: 1.06, 1.07

**Estimate**: 2h

---

## 1.09 — Signup creates tenant

**Description**: On new user signup, automatically create a `tenants` row and link the user to it via `tenant_users`.

**Tasks**:
- Create Supabase database function `handle_new_user()` triggered on `auth.users` insert
- Function creates a new `tenants` row with default values
- Function inserts a `tenant_users` row linking the user as owner
- Set default `provider_config` JSONB to India English stack
- Set default `language = 'en'`, `market = 'india_english'`
- Add migration that registers the trigger

**Acceptance criteria**:
- New signup automatically creates exactly one tenant
- User is linked as `owner` role
- Default `provider_config` is the India English stack
- Trigger runs in under 50ms
- Re-running signup for the same email does not create duplicate tenant

**Dependencies**: 1.04, 1.06

**Estimate**: 2h

---

## 1.10 — FastAPI base structure

**Description**: Set up FastAPI app with structured routing, asyncpg connection pool, and Pydantic models.

**Tasks**:
- Create app structure: `/routes`, `/models`, `/db`, `/services`, `/providers`
- Set up asyncpg connection pool with retry logic
- Create Pydantic v2 models for `Tenant`, `User`, `Agent`, `Call`
- Add CORS middleware for the Vercel frontend
- Add request ID middleware for logging
- Configure structlog with JSON output

**Acceptance criteria**:
- App boots without errors via `uvicorn`
- Connection pool initializes against Supabase
- Pydantic models match DB schema
- CORS allows requests from configured frontend origins
- Logs come out as structured JSON

**Dependencies**: 1.01, 1.03

**Estimate**: 3h

---

## 1.11 — JWT auth middleware

**Description**: Verify Supabase JWT on every authenticated request and attach user + tenant context to the request.

**Tasks**:
- Implement JWT verification using Supabase's public JWKS
- Create FastAPI dependency `get_current_user()` that extracts user from token
- Create dependency `get_current_tenant()` that loads tenant via `tenant_users`
- Handle expired tokens, missing tokens, invalid signatures
- Add error responses (401, 403) with consistent format
- Cache JWKS for 10 minutes to avoid hot-path latency

**Acceptance criteria**:
- Valid token returns user object
- Expired token returns 401
- Missing token returns 401
- Token without tenant returns 403
- JWKS cache works (verified by log inspection)

**Dependencies**: 1.10

**Estimate**: 3h

---

## 1.12 — /me and /health endpoints

**Description**: Build the two foundational backend endpoints used by every other phase.

**Tasks**:
- Implement `GET /health` returning `{status: "ok", timestamp}`
- Implement `GET /me` returning user + tenant + role
- Add Pydantic response models
- Add OpenAPI tags and descriptions
- Write integration test for both
- Verify both work in deployed environment

**Acceptance criteria**:
- `/health` returns 200 in under 100ms
- `/me` returns full user + tenant payload when authenticated
- `/me` returns 401 without auth
- OpenAPI docs render at `/docs`
- Integration tests pass in CI

**Dependencies**: 1.11

**Estimate**: 2h

---

## 1.13 — Service-role client and internal-user check

**Description**: Build a Supabase service-role client for trusted backend writes and a check for whether the current user is an internal team member.

**Tasks**:
- Create service-role Supabase client (uses `SUPABASE_SERVICE_ROLE_KEY`)
- Add FastAPI dependency `require_internal_user()`
- Implement check that queries `internal_users` table for the current user
- Add helper to write to `audit_log` from any internal-user action
- Document when to use service-role vs user-scoped client

**Acceptance criteria**:
- Service-role client can bypass RLS
- `require_internal_user()` returns user when in `internal_users`, else 403
- Audit log helper writes actor + action + payload + timestamp
- Service-role key never exposed to frontend code
- Helper is reusable across all internal routes

**Dependencies**: 1.11

**Estimate**: 2h

---

## 1.14 — Marketing landing page

**Description**: Build a basic marketing landing page with hero, features, and CTA buttons.

**Tasks**:
- Design hero section with headline, subheadline, CTA
- Add features section (3-4 cards)
- Add "How it works" 3-step section
- Add footer with links
- Make responsive for mobile
- Add SEO meta tags

**Acceptance criteria**:
- Page renders correctly on desktop and mobile
- All CTAs link to `/signup` or `/login`
- Lighthouse score above 90 on performance
- Meta tags include title, description, og:image
- No console errors

**Dependencies**: 1.07

**Estimate**: 3h

---

## 1.15 — Empty client portal shell

**Description**: Build the navigation shell and placeholder for the client portal that Phase 5 will populate.

**Tasks**:
- Build sidebar navigation (Dashboard, Calls, Knowledge, Settings)
- Build top header with user dropdown + sign-out
- Create placeholder pages for each nav item
- Add "Coming soon" state for empty dashboard
- Wire user info to `/me` endpoint
- Make responsive

**Acceptance criteria**:
- Sidebar shows current page highlighted
- User dropdown shows name and sign-out works
- All placeholder pages route correctly
- Mobile menu works
- Portal layout consistent across all pages

**Dependencies**: 1.08, 1.12

**Estimate**: 3h

---

## 1.16 — Empty internal dashboard shell

**Description**: Build the navigation shell for the internal dashboard that Phase 3 will populate.

**Tasks**:
- Build sidebar navigation (Tenants, Calls, Audit Log, Metrics)
- Build top header with internal-user dropdown
- Create placeholder pages for each nav item
- Add visual distinction from client portal (different color accent)
- Wire internal-user check to redirect tenant users
- Make responsive

**Acceptance criteria**:
- Internal dashboard visually distinct from client portal
- Sidebar navigation works
- Placeholder pages route correctly
- Tenant user accessing `/internal` redirects to login
- Sign-out works

**Dependencies**: 1.08, 1.13

**Estimate**: 3h

---

## 1.17 — Render deployment + warm-ping

**Description**: Deploy FastAPI to Render and configure external cron to prevent free-tier idle sleep.

**Tasks**:
- Create Render web service pointing at GitHub repo
- Set Singapore region for proximity to Indian users
- Configure environment variables (Supabase URL, keys, etc.)
- Set up auto-deploy from `main` branch
- Configure cron-job.org to hit `/health` every 10 minutes
- Verify service stays warm for 24h continuously

**Acceptance criteria**:
- FastAPI accessible at production URL
- Auto-deploy works on push to `main`
- Cron ping verified hitting `/health` every 10 min
- Service responds in under 200ms after being idle 30+ min
- Logs visible in Render dashboard

**Dependencies**: 1.12

**Estimate**: 2h

---

## 1.18 — Vercel deployment + domain

**Description**: Deploy Next.js to Vercel and wire custom domain with subdomains.

**Tasks**:
- Connect GitHub repo to Vercel project
- Configure environment variables for production
- Set up auto-deploy from `main`
- Point apex domain at Vercel
- Configure `app.` subdomain for portal routing
- Configure `api.` subdomain to proxy Render service

**Acceptance criteria**:
- Apex domain shows marketing site
- `app.yourdomain.ai` shows portal (after login)
- `api.yourdomain.ai/health` returns 200
- TLS certificates valid on all subdomains
- Auto-deploy fires on push to `main`

**Dependencies**: 1.14, 1.17

**Estimate**: 2h

---

## 1.19 — Phase 1 complete testing

**Description**: End-to-end testing of all Phase 1 deliverables before moving to Phase 2.

**Tasks**:
- Run cross-tenant smoke test against production DB
- Test full signup → email confirm → login → portal flow
- Test internal-user login → internal dashboard flow
- Test sign-out from both portals
- Verify all environment variables set in Vercel and Render
- Verify RLS active on all tenant-scoped tables
- Run Lighthouse on landing page (target 90+)
- Walk through every route guard scenario
- Confirm warm-ping has kept Render warm 24h+
- Document any bugs found and fix or ticket

**Acceptance criteria**:
- Signup → confirmation → login works end-to-end
- Two test tenants confirmed isolated
- Internal-user role separation works
- All routes return correct status codes
- Production deployments stable for 48h+
- No P0 bugs open

**Dependencies**: 1.05, 1.09, 1.15, 1.16, 1.18

**Estimate**: 3h

---

# Phase 2 — Voice pipeline

Voice pipeline week. First end-to-end AI call from a real phone with hardcoded single-tenant config.

---

## 2.01 — Twilio account setup and number purchase

**Description**: Provision Twilio account, complete India number verification, and purchase the first phone number for development.

**Tasks**:
- Complete Twilio India number verification (KYC docs)
- Purchase one India local number for dev testing
- Configure number for voice + SMS capabilities
- Save Twilio Account SID, Auth Token, API Key in Render secrets
- Save the same in Vercel for any frontend-side needs
- Document phone number purchase flow for Phase 3 automation

**Acceptance criteria**:
- Twilio account verified and out of trial
- One India number purchased and active
- Credentials stored as secrets, not in code
- Number visible in Twilio console with full capabilities
- Test SMS sends successfully from this number

**Dependencies**: None

**Estimate**: 2h (mostly waiting on Twilio verification)

---

## 2.02 — Twilio webhook handler scaffold

**Description**: Build the FastAPI endpoint that Twilio hits when a call comes in, returning TwiML that opens a Media Streams websocket.

**Tasks**:
- Create `POST /webhooks/twilio/voice` endpoint
- Validate Twilio request signature using auth token
- Return TwiML with `<Connect><Stream>` pointing at backend websocket URL
- Add status callback handler at `POST /webhooks/twilio/status`
- Log incoming webhook payloads for debugging
- Handle missing or invalid signatures with 403

**Acceptance criteria**:
- Endpoint returns valid TwiML XML
- Twilio signature verification works
- Invalid signatures rejected with 403
- Status callback receives call completion events
- All webhook payloads logged with request ID

**Dependencies**: 1.10, 2.01

**Estimate**: 2h

---

## 2.03 — ngrok dev tunnel + Twilio dev config

**Description**: Set up ngrok or similar for local development so Twilio can reach the local FastAPI instance.

**Tasks**:
- Install ngrok or alternative tunnel tool
- Configure stable subdomain for repeatable testing
- Point Twilio number webhook at ngrok URL during dev
- Document the dev tunnel setup in README
- Add `.env.local` template with ngrok URL placeholder
- Create script to start ngrok + FastAPI together

**Acceptance criteria**:
- Twilio can reach local FastAPI through ngrok
- A test call to the dev number hits local webhook
- README explains dev tunnel setup clearly
- Script starts both ngrok and FastAPI with one command
- Switching between dev and production webhook URLs documented

**Dependencies**: 2.02

**Estimate**: 1h

---

## 2.04 — Pipecat installation and minimal pipeline

**Description**: Install Pipecat as a Python dependency and build a minimal pipeline that connects to Twilio Media Streams.

**Tasks**:
- Add Pipecat and dependencies to `pyproject.toml`
- Create `/services/voice/pipeline.py` for pipeline definitions
- Build minimal pipeline with Twilio transport + a static "hello" output
- Connect pipeline to a FastAPI websocket endpoint
- Handle websocket lifecycle (connect, disconnect, error)
- Add basic logging for pipeline events

**Acceptance criteria**:
- Pipecat imports cleanly with no version conflicts
- Websocket endpoint accepts Twilio Media Streams connections
- Static audio plays back to caller (any sound)
- Disconnect handled cleanly without orphan processes
- Pipeline lifecycle events logged

**Dependencies**: 2.02, 2.03

**Estimate**: 4h (research + integration)

---

## 2.05 — Audio format conversion (mulaw ↔ PCM)

**Description**: Implement audio format conversion between Twilio (mulaw 8kHz) and Cartesia/Inworld (PCM 16kHz).

**Tasks**:
- Verify Pipecat's built-in audio converters handle mulaw to PCM
- Set up resampling from 8kHz to 16kHz (and back)
- Test round-trip conversion with a known audio sample
- Add monitoring for audio buffer underruns
- Document audio pipeline in code comments
- Fix any clipping or artifacts in conversion

**Acceptance criteria**:
- Twilio mulaw audio converts to PCM 16kHz cleanly
- Round-trip back to mulaw 8kHz with no audible degradation
- No buffer underruns or audio glitches on test calls
- Conversion adds under 50ms latency
- Pipeline handles audio at production sample rates

**Dependencies**: 2.04

**Estimate**: 3h

---

## 2.06 — Provider abstraction layer

**Description**: Build the protocol interfaces and registry that `design.md` §4 specifies, even though only one impl per role wires up in Phase 2.

**Tasks**:
- Create `STTProvider`, `TTSProvider`, `LLMProvider` Python protocols
- Define shared Pydantic models: `Transcript`, `Message`, `ToolCall`, `LLMResponse`
- Create provider registry dict mapping names to classes
- Implement `make_pipeline(tenant)` factory function
- Add stub classes for `SarvamSTT`, `TogetherDeepSeekLLM` that raise `NotImplementedError`
- Document the abstraction pattern in `/services/voice/providers/README.md`

**Acceptance criteria**:
- All three protocols defined with full method signatures
- Registry resolves provider names to classes
- Factory function returns a valid Pipeline given a tenant
- Stub classes raise clear errors
- Unit tests verify the resolution logic

**Dependencies**: 1.10

**Estimate**: 3h

---

## 2.07 — InworldTTS provider implementation

**Description**: Implement the `TTSProvider` protocol for Inworld TTS-1.5 Mini with streaming synthesis.

**Tasks**:
- Set up Inworld API credentials and add to secrets
- Implement `synthesize()` method returning async iterator of audio chunks
- Configure voice ID, language, and streaming format
- Handle API errors with retry logic
- Add latency logging per synthesis request
- Test with various text lengths (5 to 200 words)

**Acceptance criteria**:
- TTS synthesizes "Hello world" to playable audio
- Streaming works (chunks arrive incrementally)
- Audio plays back through Twilio without distortion
- API errors trigger retry with exponential backoff
- Per-request latency logged

**Dependencies**: 2.06

**Estimate**: 3h

---

## 2.08 — CartesiaSTT provider implementation

**Description**: Implement the `STTProvider` protocol for Cartesia Ink-Whisper streaming STT.

**Tasks**:
- Set up Cartesia API credentials in secrets
- Implement `connect()` and `stream()` methods using websockets
- Return async iterator of `Transcript` objects (partial + final)
- Handle reconnection if websocket drops
- Add latency logging from audio in to transcript out
- Verify language config (English India)

**Acceptance criteria**:
- STT transcribes a 5-second test audio clip correctly
- Partial transcripts arrive before final
- Final transcript has high confidence on clear audio
- Reconnect logic works if websocket disconnects
- Latency under 300ms for short utterances

**Dependencies**: 2.06

**Estimate**: 3h

---

## 2.09 — DeepSeekNativeLLM provider implementation

**Description**: Implement the `LLMProvider` protocol for DeepSeek V4 Flash via the OpenAI-compatible native API.

**Tasks**:
- Set up DeepSeek API credentials in secrets
- Use `openai` SDK with `base_url` set to DeepSeek endpoint
- Implement `chat()` method supporting tools, max_tokens, system prompt
- Add prompt caching by keeping system prompt prefix stable
- Handle rate limits and timeouts
- Add token usage logging per call

**Acceptance criteria**:
- LLM returns a coherent response to "Hello, who are you?"
- Tool calling works for a test tool schema
- Cache hit verified via response metadata (lower cost on repeat)
- Rate limit errors trigger backoff
- Token usage logged for cost tracking

**Dependencies**: 2.06

**Estimate**: 3h

---

## 2.10 — VAD and turn detection

**Description**: Configure voice activity detection and turn detection in the Pipecat pipeline so the agent only responds when the caller has stopped speaking.

**Tasks**:
- Enable Silero VAD in Pipecat pipeline
- Tune VAD threshold for Indian English speech patterns
- Configure turn detection to wait for end-of-speech
- Set timeout for turn-end (e.g., 800ms of silence)
- Test with various speaking patterns (fast, slow, with pauses)
- Tune to avoid premature interruption of caller

**Acceptance criteria**:
- Agent waits for caller to finish before responding
- Caller pauses within a sentence don't trigger response
- End-of-turn detected within 1 second of caller stopping
- No false-positive interruptions during typical speech
- Tunable parameters documented

**Dependencies**: 2.05, 2.08

**Estimate**: 3h

---

## 2.11 — Barge-in handling

**Description**: Allow the caller to interrupt the agent mid-response and have the agent stop talking and listen.

**Tasks**:
- Configure Pipecat barge-in detection
- Implement immediate TTS stop when caller speech detected
- Drop any pending LLM/TTS output when interrupted
- Resume listening for new caller input
- Test with overlapping caller speech
- Verify no audio artifacts on interruption

**Acceptance criteria**:
- Caller can interrupt agent mid-sentence
- Agent stops talking within 200ms of caller speaking
- Pending TTS audio discarded cleanly
- Agent processes new caller utterance correctly
- No echo or stuck-state behavior after interruption

**Dependencies**: 2.07, 2.10

**Estimate**: 2h

---

## 2.12 — Full pipeline integration (STT + LLM + TTS)

**Description**: Wire all three providers into the Pipecat pipeline with a hardcoded system prompt and verify end-to-end conversation works.

**Tasks**:
- Connect Cartesia STT → DeepSeek LLM → Inworld TTS in pipeline
- Add a hardcoded test system prompt (e.g., "You are a helpful AI receptionist")
- Wire transcripts to LLM input and LLM output to TTS input
- Add conversation memory (last 10 turns kept in context)
- Log every turn (user input, LLM output, latencies)
- Test with a real phone call

**Acceptance criteria**:
- Caller can have a 5-turn back-and-forth conversation
- Each turn's round-trip under 1.2s on the 90th percentile
- Conversation memory works (agent references earlier turns)
- Logs show clean per-turn breakdown
- No dropped turns or stuck states

**Dependencies**: 2.09, 2.11

**Estimate**: 4h

---

## 2.13 — Call lifecycle and DB writes

**Description**: Write a `calls` row when a call starts, update it on call end, and write `call_messages` per turn.

**Tasks**:
- On Twilio webhook, insert `calls` row with `started_at`, `twilio_call_sid`, hardcoded tenant/agent IDs for now
- After each turn, insert `call_messages` row with role, content, latency
- On status callback "completed", update `calls` with `ended_at`, `duration_secs`
- Capture `provider_snapshot` JSONB recording which providers were used
- Handle edge case: call drops before status callback
- Add database indexes for common query patterns

**Acceptance criteria**:
- Every call creates exactly one `calls` row
- Every turn creates exactly one `call_messages` row
- Call completion updates `ended_at` and `duration_secs`
- `provider_snapshot` captures all three provider names
- Dropped calls still get their row closed (via timeout job)

**Dependencies**: 1.03, 2.12

**Estimate**: 3h

---

## 2.14 — Call recording to Supabase Storage

**Description**: Download the call recording from Twilio after call completion and upload to Supabase Storage.

**Tasks**:
- Enable recording on the Twilio number
- Add background job triggered on status callback
- Download recording from Twilio recording URL
- Upload to Supabase Storage with path `recordings/{tenant_id}/{call_id}.mp3`
- Update `calls.recording_url` with storage path
- Verify recording playback works

**Acceptance criteria**:
- Recording exists in Supabase Storage after call ends
- `calls.recording_url` points to the right path
- Recording playable via signed URL
- Background job retries on transient Twilio errors
- Storage bucket has correct access policies

**Dependencies**: 2.13

**Estimate**: 3h

---

## 2.15 — Per-turn latency logging

**Description**: Capture detailed latency metrics for every turn so bottlenecks can be diagnosed.

**Tasks**:
- Add timestamps at: audio in, STT final, LLM start, LLM end, TTS start, TTS first byte, TTS last byte
- Compute per-segment latencies (STT time, LLM time, TTS time, total)
- Write to `call_messages.latency_ms` (total) and a separate JSONB for the breakdown
- Add an internal endpoint to query p50/p95/p99 per provider
- Log warning if any turn exceeds 1.5s total
- Document the latency schema

**Acceptance criteria**:
- Every `call_messages` row has `latency_ms` populated
- Breakdown JSONB shows STT, LLM, TTS components
- Internal endpoint returns p50/p95/p99 over last 100 turns
- Slow turns log a warning with breakdown
- Schema documented in `/docs` or code comments

**Dependencies**: 2.13

**Estimate**: 2h

---

## 2.16 — Greeting on call pickup

**Description**: Play a TTS-generated greeting immediately when the call connects, before the caller speaks.

**Tasks**:
- Add greeting step at pipeline start (before STT activation)
- Use the system prompt to derive an initial greeting
- TTS-synthesize and play immediately on websocket open
- Ensure greeting plays in under 800ms from call connect
- Handle case where caller starts speaking during greeting (barge-in works)
- Test greeting variants with different prompts

**Acceptance criteria**:
- Caller hears greeting within 800ms of call connecting
- Greeting is coherent and matches the system prompt
- Caller can interrupt greeting via barge-in
- No silent gap between connect and greeting
- Greeting plays exactly once per call

**Dependencies**: 2.12

**Estimate**: 2h

---

## 2.17 — Pre-call consent disclosure

**Description**: Play a consent disclosure ("This call may be recorded for quality and AI assistance") before the AI agent starts.

**Tasks**:
- Pre-generate consent audio file or use TTS at call start
- Add a TwiML `<Play>` or `<Say>` verb before `<Connect>`
- Disclosure should be 3-5 seconds, clear and audible
- Test in both directions (caller hears it, recording captures it)
- Allow disclosure text to be configurable per market (for v2)
- Verify legal-friendly wording

**Acceptance criteria**:
- Every inbound call hears the disclosure before AI greeting
- Disclosure is in English and clearly audible
- Disclosure captured in the call recording
- Disclosure adds under 5s to total call setup time
- Wording reviewed for legal compliance

**Dependencies**: 2.02

**Estimate**: 1.5h

---

## 2.18 — Agent process lifecycle

**Description**: Manage Pipecat agent process lifecycle: spawn on call start, clean up on call end or error.

**Tasks**:
- Track active agents in an in-memory registry keyed by `call_sid`
- Spawn agent on websocket connect, register it
- On call end (status callback or websocket close), kill the agent
- Add timeout to force-kill agents idle past 30 minutes
- Handle crashes — orphan agents detected by periodic sweep
- Add metrics: active agent count

**Acceptance criteria**:
- Active agent count visible via internal endpoint
- Agents always terminated on call end
- No orphan processes after 1 hour of normal traffic
- Crashed agents detected and cleaned up
- Force-kill works at 30-minute timeout

**Dependencies**: 2.12

**Estimate**: 3h

---

## 2.19 — Phase 2 complete testing

**Description**: End-to-end testing of the voice pipeline before moving to Phase 3.

**Tasks**:
- Make 10+ real test calls from different phones
- Verify p90 per-turn latency under 1.2 seconds
- Verify all `calls` and `call_messages` rows written correctly
- Verify recordings appear in Supabase Storage
- Test barge-in across multiple call scenarios
- Test long calls (5+ minutes) and verify stability
- Test rapid-fire short calls (back-to-back) for resource leaks
- Test edge case: caller hangs up mid-response
- Test edge case: provider API timeout
- Check active agent count returns to zero after calls end
- Verify consent disclosure plays on every call

**Acceptance criteria**:
- 10 successful test calls with no critical bugs
- p90 latency under 1.2s
- Zero orphan agent processes after test run
- All recordings retrievable from storage
- Latency breakdown shows no single component over budget
- Provider failures degrade gracefully (caller doesn't hear silence)

**Dependencies**: 2.14, 2.15, 2.16, 2.17, 2.18

**Estimate**: 4h

---

*End of tickets.md*
