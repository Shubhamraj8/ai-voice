# Tickets

Development tickets organized by phase. Each ticket follows the naming convention `<phase>.<number>` and includes description, tasks, acceptance criteria, dependencies on other tickets, and an estimate in hours (assuming AI-IDE-assisted coding).

Companion to `mvp-planning.md`, `features.md`, `design.md`, and `roadmap.md`.

---

## Contents

- [Phase 1 — Foundation](#phase-1--foundation)
- [Phase 2 — Voice pipeline](#phase-2--voice-pipeline)
- [Phase 3 — Internal dashboard and multi-tenancy](#phase-3--internal-dashboard-and-multi-tenancy)
- [Phase 4 — Business brain (knowledge + tools)](#phase-4--business-brain-knowledge--tools)
- [Phase 5 — Client portal, billing, and compliance](#phase-5--client-portal-billing-and-compliance)

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

**Description**: Implement audio format conversion between Twilio (mulaw 8kHz) and Deepgram (linear16 PCM, 16kHz for STT input, 8kHz for TTS output back to Twilio).

**Tasks**:

- Verify Pipecat's built-in audio converters handle mulaw to PCM
- Set up resampling from 8kHz to 16kHz for STT ingress
- Configure Deepgram TTS to emit `linear16` 8kHz directly (avoid a downsample on egress)
- Test round-trip conversion with a known audio sample
- Add monitoring for audio buffer underruns
- Document audio pipeline in code comments
- Fix any clipping or artifacts in conversion

**Acceptance criteria**:

- Twilio mulaw audio converts to PCM 16kHz cleanly for Deepgram STT
- Deepgram TTS audio plays back through Twilio without distortion
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
- Create provider registry dict mapping names to classes (`design.md` §4 layout)
- Implement `make_pipeline(tenant)` factory function that reads `tenant.provider_config`
- Add stub classes for `DeepgramSTTEnterprise`, `DeepgramTTSEnterprise`, `SarvamSTT`, `SarvamTTS`, `TogetherDeepSeekLLM` that raise `NotImplementedError`
- Document the abstraction pattern in `/services/voice/providers/README.md`

**Acceptance criteria**:

- All three protocols defined with full method signatures
- Registry resolves provider names to classes
- Factory function returns a valid Pipeline given a tenant
- Stub classes raise clear errors that name the future phase that will implement them
- Unit tests verify the resolution logic (including the default India English stack: `deepgram` + `deepgram` + `deepseek_native`)

**Dependencies**: 1.10

**Estimate**: 3h

---

## 2.07 — DeepgramTTS provider implementation (Aura-1)

**Description**: Implement the `TTSProvider` protocol for Deepgram Aura-1 streaming TTS over the WebSocket Speak API.

**Tasks**:

- Set up Deepgram API key and add to Render secrets
- Add `deepgram-sdk` to `pyproject.toml`
- Implement `synthesize()` method returning async iterator of audio chunks
- Configure model `aura-asteria-en` (default Indian-English-friendly voice), encoding `linear16`, sample rate `8000` to match Twilio
- Track `tts_chars` per synthesis call and emit it on a metrics channel for per-turn cost calculation (Aura-1 bills $0.015 / 1k chars)
- Handle API errors with retry + exponential backoff
- Add latency logging per synthesis request (time-to-first-byte and time-to-last-byte)
- Test with various text lengths (5 to 200 words) and verify the "concise reply" budget (≤25 words / ~150 chars per turn) holds

**Acceptance criteria**:

- TTS synthesizes "Hello, how can I help you today?" to playable audio
- Streaming works — first audio byte arrives in under 350ms p95
- Audio plays back through Twilio without distortion at 8kHz
- API errors trigger retry with exponential backoff
- Per-request latency and `tts_chars` count logged for every turn
- Voice catalog options (`aura-asteria-en`, `aura-luna-en`, `aura-stella-en`, `aura-athena-en`, `aura-hera-en`, `aura-orion-en`, `aura-arcas-en`, `aura-perseus-en`, `aura-angus-en`, `aura-orpheus-en`, `aura-helios-en`, `aura-zeus-en`) documented in `/services/voice/providers/README.md` for the Phase 3 agent edit form

**Dependencies**: 2.06

**Estimate**: 3h

---

## 2.08 — DeepgramSTT provider implementation (Nova-3 Monolingual streaming)

**Description**: Implement the `STTProvider` protocol for Deepgram Nova-3 Monolingual streaming STT over the WebSocket Listen API.

**Tasks**:

- Reuse Deepgram credentials from 2.07
- Implement `connect()` and `stream()` methods using the Deepgram WSS streaming endpoint
- Return async iterator of `Transcript` objects (partial + final) via Deepgram's `interim_results`
- Configure model `nova-3`, language `en` (India English handled by Nova-3 Monolingual English), `smart_format=true`, `endpointing=300` (ms)
- Enable `vad_events` so end-of-utterance signals integrate with Pipecat turn detection
- Handle reconnection if websocket drops (close codes 1006, 1011)
- Add latency logging from audio in to final transcript out

**Acceptance criteria**:

- STT transcribes a 5-second test audio clip correctly on Indian-accent English
- Partial transcripts arrive before final (verified via log inspection)
- Final transcript has high confidence (≥0.85) on clear audio
- Reconnect logic works if websocket disconnects mid-call
- Latency under 300ms p95 from `is_final=true` event to local `Transcript` emission
- Promotional rate ($0.0048/min PAYG) confirmed in invoice after first dev calls

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
- Configure turn detection to wait for end-of-speech (combine Silero with Deepgram `vad_events`)
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
- Implement immediate TTS stop when caller speech detected (close Deepgram TTS websocket cleanly to avoid wasted characters being billed)
- Drop any pending LLM/TTS output when interrupted
- Resume listening for new caller input
- Test with overlapping caller speech
- Verify no audio artifacts on interruption

**Acceptance criteria**:

- Caller can interrupt agent mid-sentence
- Agent stops talking within 200ms of caller speaking
- Pending TTS audio discarded cleanly
- Interrupted TTS calls don't continue streaming (and don't keep billing characters) after barge-in
- Agent processes new caller utterance correctly
- No echo or stuck-state behavior after interruption

**Dependencies**: 2.07, 2.10

**Estimate**: 2h

---

## 2.12 — Full pipeline integration (STT + LLM + TTS)

**Description**: Wire all three providers into the Pipecat pipeline with a hardcoded system prompt and verify end-to-end conversation works.

**Tasks**:

- Connect Deepgram Nova-3 STT → DeepSeek V4 Flash LLM → Deepgram Aura-1 TTS in the pipeline
- Add a hardcoded test system prompt (e.g., "You are a helpful AI receptionist. Keep replies under 25 words.")
- Wire transcripts to LLM input and LLM output to TTS input
- Add conversation memory (last 10 turns kept in context)
- Log every turn (user input, LLM output, latencies, `tts_chars`)
- Test with a real phone call

**Acceptance criteria**:

- Caller can have a 5-turn back-and-forth conversation
- Each turn's round-trip under 1.2s on the 90th percentile
- Conversation memory works (agent references earlier turns)
- Logs show clean per-turn breakdown (STT ms / LLM ms / TTS first-byte ms / total ms / `tts_chars`)
- No dropped turns or stuck states
- Concise-reply budget holds — average `tts_chars` per turn stays under 200

**Dependencies**: 2.09, 2.11

**Estimate**: 4h

---

## 2.13 — Call lifecycle and DB writes

**Description**: Write a `calls` row when a call starts, update it on call end, and write `call_messages` per turn.

**Tasks**:

- On Twilio webhook, insert `calls` row with `started_at`, `twilio_call_sid`, hardcoded tenant/agent IDs for now
- After each turn, insert `call_messages` row with role, content, latency
- On status callback "completed", update `calls` with `ended_at`, `duration_secs`
- Capture `provider_snapshot` JSONB recording which providers were used (e.g. `{"stt": "deepgram", "tts": "deepgram", "llm": "deepseek_native"}`)
- Also persist per-turn `tts_chars` on `call_messages` for Phase 4 cost calculation
- Handle edge case: call drops before status callback
- Add database indexes for common query patterns

**Acceptance criteria**:

- Every call creates exactly one `calls` row
- Every turn creates exactly one `call_messages` row
- Call completion updates `ended_at` and `duration_secs`
- `provider_snapshot` captures all three provider names
- `tts_chars` populated on every assistant-role `call_messages` row
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
- Confirm Deepgram $200 free credit is being drawn down on the dashboard and project a paid run-rate from the early call sample

**Acceptance criteria**:

- 10 successful test calls with no critical bugs
- p90 latency under 1.2s
- Zero orphan agent processes after test run
- All recordings retrievable from storage
- Latency breakdown shows no single component over budget
- Provider failures degrade gracefully (caller doesn't hear silence)
- Deepgram credit consumption visible in console and matches the dev call volume within ±10%

**Dependencies**: 2.14, 2.15, 2.16, 2.17, 2.18

**Estimate**: 4h

---

# Phase 3 — Internal dashboard and multi-tenancy

Multi-tenancy week. Convert the single hardcoded tenant from Phase 2 into a real tenant table managed through the internal dashboard. Two tenants on two different Twilio numbers should each get their own agent, voice, and prompt.

---

## 3.01 — Internal user role and seed

**Description**: Finalize the `internal_users` table started in Phase 1, add role enum (`admin`, `support`), and seed the first internal user (you).

**Tasks**:

- Add `role` enum column to `internal_users` if not already present
- Write migration to seed the founding internal user from a `INTERNAL_USER_EMAIL` env var on first deploy
- Update `require_internal_user()` to also expose role on the request context
- Add helper `require_internal_role(role)` for routes that need admin specifically
- Document how to add a new internal user manually via SQL

**Acceptance criteria**:

- Founding internal user can sign up via the normal auth flow and is auto-promoted on first login
- `require_internal_user()` blocks tenant-only users with 403
- `require_internal_role("admin")` blocks support-role users with 403
- No way to self-promote via the public API
- Manual SQL escalation procedure documented in `/packages/db/README.md`

**Dependencies**: 1.13

**Estimate**: 2h

---

## 3.02 — Internal login UX

**Description**: Polish the internal-only login flow so it's visually and behaviorally distinct from the tenant login.

**Tasks**:

- Add a `/internal/login` page (separate route from `/login`)
- Apply the internal-dashboard accent theme so it's obviously not the tenant portal
- Redirect any internal user who lands on `/login` to `/internal` after auth
- Block tenant-only users from `/internal/login` with a "you don't have access" page
- Add "request access" mailto link for non-internal users who land here by mistake

**Acceptance criteria**:

- `/internal/login` visually distinct from `/login`
- Internal users land on `/internal` after success
- Tenant users see a clear access-denied page (not a redirect loop)
- The login surface is link-only (not crawlable from the marketing site)

**Dependencies**: 1.08, 3.01

**Estimate**: 2h

---

## 3.03 — Tenant CRUD API endpoints

**Description**: Build the FastAPI endpoints the internal dashboard will use to list, view, create, and update tenants.

**Tasks**:

- `GET /internal/tenants` — paginated list with filters (status, market, search)
- `GET /internal/tenants/{id}` — single tenant with linked agents and recent call summary
- `POST /internal/tenants` — create tenant with default `provider_config` for selected market
- `PATCH /internal/tenants/{id}` — update name, status, `provider_config`, contact info
- All routes protected by `require_internal_user()`
- All writes append a row to `audit_log` via the helper from 1.13

**Acceptance criteria**:

- All four endpoints return correct shapes documented in OpenAPI
- Pagination works (default 25 per page, max 100)
- Search matches on name, contact email, phone number
- `provider_config` validated against the known provider registry (rejects unknown keys)
- Every write produces an audit log row with the internal user's ID

**Dependencies**: 1.13, 3.01

**Estimate**: 3h

---

## 3.04 — Tenant list page

**Description**: Build the internal dashboard list view of all tenants.

**Tasks**:

- Replace the placeholder `/internal/tenants` page from 1.16 with a real table
- Columns: name, market, status (active / paused / churned), agent count, calls last 7d, MRR
- Filter chips: market, status, has-active-calls
- Search box wired to backend search
- Click row → tenant detail page
- "New tenant" button top-right opens the create form (3.06)

**Acceptance criteria**:

- All tenants render with correct columns
- Filters narrow results without page reload
- Search debounced to 300ms
- Empty state shows "No tenants yet — create one" CTA
- Sortable by created date, MRR, calls

**Dependencies**: 1.16, 3.03

**Estimate**: 3h

---

## 3.05 — Tenant detail page

**Description**: Build the per-tenant detail page that internal staff use to inspect, configure, and troubleshoot a tenant.

**Tasks**:

- Header: tenant name, market, status, contact, edit/pause buttons
- Tabs: Overview, Agents, Calls, Knowledge (placeholder for Phase 4), Billing (placeholder for Phase 5), Audit
- Overview tab: provider_config display, call volume sparkline (last 14 days), latest 5 calls
- Agents tab: list of linked agents with edit links (form built in 3.08)
- Calls tab: paginated list of this tenant's calls (reuses Phase 2 data)
- Audit tab: filtered audit log for this tenant

**Acceptance criteria**:

- Page loads under 1s for a tenant with ~1000 calls
- Provider config editable inline (writes through 3.03 PATCH)
- All linked data scoped to this tenant (no leakage)
- Tab state preserved in URL (`?tab=agents`)
- Audit tab paginated, newest first

**Dependencies**: 3.03

**Estimate**: 4h

---

## 3.06 — Tenant create form (with Twilio number provisioning)

**Description**: Build the form that creates a tenant and provisions its first Twilio phone number in one flow.

**Tasks**:

- Modal form on the tenant list page: name, contact name, contact email, market dropdown (india_english, india_hindi, us_hipaa for v3 pre-prov), Twilio number purchase region (defaults to India)
- On submit:
  - Search Twilio for available numbers in the chosen region
  - Show 3-5 candidate numbers, let internal user pick one
  - Purchase the chosen number via Twilio API
  - Insert tenant row with default provider_config for the selected market
  - Configure the purchased number's voice webhook to point at `POST /webhooks/twilio/voice`
- Audit log the creation + the number purchase + the cost ($1.15/mo for India local)
- Surface Twilio errors gracefully (insufficient funds, KYC missing, etc.)

**Acceptance criteria**:

- New tenant + new Twilio number live in under 30 seconds
- The purchased number is reachable: a test call hits Phase 2's webhook handler
- Failed purchases roll back the tenant insert (transactional)
- All three audit rows written (create_tenant, purchase_number, configure_webhook)
- Form re-shows candidate numbers if the user wants to pick a different one

**Dependencies**: 2.01, 3.03

**Estimate**: 4h

---

## 3.07 — Agent CRUD API endpoints

**Description**: Build the FastAPI endpoints for creating, reading, updating, and deleting agents per tenant.

**Tasks**:

- `GET /internal/tenants/{tid}/agents` — list agents for a tenant
- `POST /internal/tenants/{tid}/agents` — create agent
- `PATCH /internal/tenants/{tid}/agents/{id}` — update agent (name, system_prompt, voice_id, tool_whitelist, status)
- `DELETE /internal/tenants/{tid}/agents/{id}` — soft delete
- All routes protected by `require_internal_user()` and tenant-scoped
- Validate `voice_id` against the Aura-1 voice catalog from 2.07
- Validate `system_prompt` length (max 4000 chars)

**Acceptance criteria**:

- CRUD works against a fresh tenant
- Invalid `voice_id` returns 422 with the list of allowed values
- Soft delete sets `deleted_at`, agent stops accepting calls but historical calls remain
- Every write produces an audit_log row
- Cross-tenant access (e.g. tenant A's user trying to read tenant B's agent) returns 403

**Dependencies**: 3.03

**Estimate**: 3h

---

## 3.08 — Agent edit form (with Aura voice catalog dropdown)

**Description**: Build the form internal staff use to edit an agent's prompt, voice, and tools.

**Tasks**:

- Form fields: name, system_prompt (textarea with character count), voice_id (dropdown), tool_whitelist (multi-select — placeholder until Phase 4 tools), status
- Voice dropdown sources from the Aura voice catalog (12 voices from 2.07), with a "preview" button that synthesizes a sample line and plays it inline
- Validate before submit: prompt non-empty, prompt under 4000 chars
- On save, write through 3.07 PATCH and show a success toast
- Add "Test call" button — generates a one-time Twilio number to call that bypasses tool execution (preview mode)

**Acceptance criteria**:

- All 12 Aura voices selectable and previewable
- Voice preview audio plays within 1.5s of clicking
- Prompt textarea shows live character count, blocks save above 4000
- Saving updates the agent and immediately affects new inbound calls
- Test-call mode marked clearly on the resulting `calls` row (`test=true`)

**Dependencies**: 2.07, 3.05, 3.07

**Estimate**: 4h

---

## 3.09 — Per-tenant webhook routing

**Description**: Convert the hardcoded tenant lookup in Phase 2's webhook handler into a real lookup by Twilio `To` number.

**Tasks**:

- Update `POST /webhooks/twilio/voice` to extract the `To` field from the Twilio payload
- Query `agents` table joined with `tenants` where `agents.phone_number = To` and both are active
- Return 404 with a graceful "this number is not configured" TwiML message if no match
- Pass the resolved tenant + agent into the websocket connection context (via a signed query param or session cookie)
- Add an index on `agents.phone_number` for fast lookups
- Log the resolution decision for every inbound call

**Acceptance criteria**:

- Tenant A's number routes to tenant A's agent, tenant B's to tenant B's
- Unknown number returns a polite "not configured" TwiML message (not a 500)
- Lookup adds under 20ms to the webhook response
- Soft-deleted agents return the "not configured" message even if their number is still on Twilio
- Logs show `resolved_tenant_id` and `resolved_agent_id` for every call

**Dependencies**: 2.02, 2.13, 3.07

**Estimate**: 3h

---

## 3.10 — make_pipeline(tenant) factory

**Description**: Replace the hardcoded provider wiring in 2.12 with a real factory that constructs a Pipecat pipeline from a tenant's `provider_config` and an agent's settings.

**Tasks**:

- Implement `make_pipeline(tenant, agent)` that:
  - Reads `tenant.provider_config` (`stt`, `tts`, `llm` keys)
  - Resolves each to a class via the registry from 2.06
  - Instantiates each with the right config (model, voice from `agent.voice_id`, language from `tenant.language`)
  - Wires them into a Pipecat pipeline with the agent's `system_prompt` and `tool_whitelist`
- Add a unit test that feeds three different `provider_config` shapes and asserts the right classes are instantiated
- Add a sanity check that all three providers are non-stub before returning (raises if a stub is referenced)
- Replace the hardcoded pipeline call in the websocket handler with `make_pipeline(tenant, agent)`

**Acceptance criteria**:

- Two tenants with different voices and prompts both work end-to-end on real calls
- Switching a tenant's provider_config in the DB takes effect on the next call (no redeploy)
- Stub providers raise a clear error at pipeline construction (not mid-call)
- Unit tests pass for the India English default and an alternate (e.g. Aura voice swap)
- No regressions on Phase 2 calls (the default config produces the same pipeline as before)

**Dependencies**: 2.06, 2.12, 3.07, 3.09

**Estimate**: 3h

---

## 3.11 — Audit log write helpers

**Description**: Generalize the audit log helper from 1.13 so every internal-user write across Phase 3 routes uses one consistent shape.

**Tasks**:

- Define `audit_log` payload schema: `actor_id`, `actor_type` (internal | tenant | system), `action`, `target_type`, `target_id`, `tenant_id`, `payload_json`, `created_at`
- Add a decorator `@audit("action_name", target_type="...")` for FastAPI routes
- Refactor 3.03, 3.06, 3.07, 3.08 to use the decorator
- Add automatic redaction for sensitive fields (auth tokens, payment info) in the payload
- Add a system-actor variant for non-user-driven writes (Phase 4/5 jobs)

**Acceptance criteria**:

- Every internal-user write writes exactly one audit row
- Audit row includes a diff of changed fields (not the full new state)
- Redaction verified for a payload containing fake API keys
- Decorator skips audit writes if the route returns a 4xx/5xx (no spurious rows)
- System-actor writes work from a background job (Phase 4 ingestion will use this)

**Dependencies**: 1.13, 3.03

**Estimate**: 2h

---

## 3.12 — Audit log viewer

**Description**: Build the `/internal/audit` page that shows the audit log with filters.

**Tasks**:

- Paginated list, newest first, default 50 per page
- Filter chips: actor type (internal / tenant / system), action, target type, date range
- Per-tenant filter usable as `?tenant=<id>` (linked from tenant detail page)
- Expandable row showing the payload diff in a code block
- Search by actor email or target ID
- Export current view as CSV

**Acceptance criteria**:

- Loads under 1s with 10k audit rows
- Filters compose (multiple at once)
- CSV export downloads with correct headers
- Per-tenant filter works when linked from tenant detail
- Expand/collapse smooth and accessible

**Dependencies**: 3.11

**Estimate**: 3h

---

## 3.13 — Two-tenant verification test

**Description**: End-to-end test that confirms two tenants on two different numbers each get their own voice, prompt, and call records, with zero cross-tenant leakage.

**Tasks**:

- Create two test tenants via 3.06 with different voices (e.g. `aura-asteria-en` and `aura-orion-en`) and different prompts
- Call tenant A's number, verify A's voice and A's prompt drive the conversation
- Call tenant B's number, verify B's voice and B's prompt drive the conversation
- Assert both calls produce `calls` rows scoped to the right tenant
- Assert RLS prevents tenant A's portal user (when Phase 5 ships) from seeing tenant B's calls
- Add this scenario to CI as a recorded-fixture test (no live phone needed)

**Acceptance criteria**:

- Two test tenants demonstrably get different voices on the same hardware
- Each tenant's audit log only shows their own writes
- `provider_snapshot` correctly captures each tenant's resolved config
- Test added to CI and runs in under 60 seconds against fixtures
- Manual phone-call playthrough recorded for the dev journal

**Dependencies**: 3.06, 3.08, 3.10

**Estimate**: 3h

---

## 3.14 — Phase 3 complete testing

**Description**: End-to-end testing of the multi-tenant flow before moving to Phase 4.

**Tasks**:

- Create three tenants through the dashboard (no SQL shortcuts)
- For each, create an agent, set a unique voice, set a unique prompt
- Make a real call to each number, verify isolation
- Edit one tenant's prompt mid-flight, verify next call picks it up
- Pause one tenant, verify their number returns "not configured"
- Verify audit log captures every action
- Run the cross-tenant RLS smoke test from 1.05 against the new schema
- Confirm `make_pipeline` returns a stub error if a tenant's provider_config references a not-yet-implemented provider

**Acceptance criteria**:

- Three tenants live, three voices, three prompts, all isolated
- Audit log shows every internal action with correct actor and tenant
- Paused tenant rejects calls gracefully
- Provider config swap takes effect within one call
- No P0 bugs open
- Deepgram credit consumption split visible per tenant via the `provider_snapshot` + duration aggregation

**Dependencies**: 3.04, 3.05, 3.06, 3.08, 3.12, 3.13

**Estimate**: 4h

---

# Phase 4 — Business brain (knowledge + tools)

Knowledge week. Agents stop being generic and start being useful for a real business — they answer from a PDF the owner uploaded and they call tools (transfer, SMS, escalate). Post-call summaries land in the call record.

---

## 4.01 — PDF upload endpoint and Storage bucket

**Description**: Build the upload pipeline that puts a PDF into Supabase Storage and records a `knowledge_documents` row.

**Tasks**:

- Create Supabase Storage bucket `knowledge` with tenant-scoped access policy
- Migration for `knowledge_documents` table (`id`, `tenant_id`, `agent_id`, `filename`, `storage_path`, `bytes`, `status`, `uploaded_at`, `processed_at`, `error`)
- `POST /internal/tenants/{tid}/knowledge` — internal upload endpoint
- Validate PDF (MIME type, max 20MB, page count under 500)
- Compute and store SHA-256 of the file for dedup
- Set initial status to `pending`

**Acceptance criteria**:

- Internal user can upload a PDF via the dashboard (UI in 4.15)
- File appears in Storage at `knowledge/{tenant_id}/{doc_id}.pdf`
- Duplicate uploads (same hash) for the same tenant are rejected with 409
- `knowledge_documents` row created with `status='pending'`
- Bucket policy verified: tenant A cannot read tenant B's files

**Dependencies**: 1.03, 3.07

**Estimate**: 3h

---

## 4.02 — knowledge_documents CRUD APIs

**Description**: Build the supporting CRUD around `knowledge_documents` so the dashboard can list, view, retry, and delete uploads.

**Tasks**:

- `GET /internal/tenants/{tid}/knowledge` — list documents
- `GET /internal/tenants/{tid}/knowledge/{id}` — detail with chunk count and error if any
- `POST /internal/tenants/{tid}/knowledge/{id}/reprocess` — re-trigger ingestion
- `DELETE /internal/tenants/{tid}/knowledge/{id}` — soft delete + cascade delete embeddings
- All routes audited via 3.11
- Show ingestion progress as `chunks_total` / `chunks_done` on the detail endpoint

**Acceptance criteria**:

- All four endpoints return correct shapes
- Reprocess endpoint flips `status` back to `pending` and enqueues the job
- Delete removes Storage file and embeddings rows transactionally
- Progress fields update during ingestion
- Audit rows produced on create, reprocess, and delete

**Dependencies**: 4.01

**Estimate**: 2h

---

## 4.03 — Ingestion job (pdfplumber + tiktoken + embeddings)

**Description**: Background job that extracts text from a PDF, chunks it, embeds the chunks, and writes them to `knowledge_embeddings`.

**Tasks**:

- Add `pdfplumber`, `tiktoken`, `openai` (for embeddings only) to `pyproject.toml`
- Implement extraction: page-by-page text via pdfplumber, dropping empty pages and headers/footers heuristically
- Chunk by tiktoken: 500-token chunks with 50-token overlap, target model `cl100k_base` encoding
- Embed each chunk via OpenAI `text-embedding-3-small` (1536 dims)
- Batch embed calls (up to 100 chunks per request) to stay efficient
- Write chunks + embeddings to `knowledge_embeddings` (schema in 4.05)
- Update `knowledge_documents.status` to `ready` on success, `error` on failure with the error string
- Run as a background worker — Phase 4 uses an asyncio task; can be promoted to a queue later

**Acceptance criteria**:

- A 30-page menu PDF processes in under 60 seconds
- Chunk count reasonable (~100 for a 30-page doc)
- Embeddings dimension is 1536
- Failed ingestion sets status to `error` with a useful message
- Re-running ingestion on the same doc replaces (not duplicates) chunks
- Token usage logged for cost (~$0.02 per 1M input tokens for text-embedding-3-small)

**Dependencies**: 4.01

**Estimate**: 4h

---

## 4.04 — pgvector setup and ivfflat index

**Description**: Configure pgvector for similarity search at production speed.

**Tasks**:

- Confirm pgvector extension enabled (from 1.03)
- Add migration for `knowledge_embeddings` table with `embedding vector(1536)` column
- Add ivfflat index with `lists = 100` (good default for under 1M rows; tune later)
- Tune `maintenance_work_mem` for index builds
- Document how to rebuild the index after a large ingest batch
- Smoke test: insert 1000 fake embeddings, query top-5, verify p95 under 50ms

**Acceptance criteria**:

- Index exists and is used by `EXPLAIN` on a similarity query
- Top-5 query under 50ms p95 with 1000 rows
- Index rebuild procedure documented
- Tenant-scoped queries filter by `tenant_id` before the vector op (uses a composite index)

**Dependencies**: 1.03

**Estimate**: 2h

---

## 4.05 — knowledge_embeddings schema + retrieval function

**Description**: Complete the embeddings schema and add a SQL function that retrieves the top-K relevant chunks for a tenant + query embedding.

**Tasks**:

- Migration for `knowledge_embeddings`: `id`, `tenant_id`, `document_id`, `chunk_index`, `content`, `token_count`, `embedding vector(1536)`, `created_at`
- Add RLS policy: tenant-user can only read their own rows; internal can read all
- Create SQL function `retrieve_knowledge(p_tenant_id uuid, p_query_embedding vector(1536), p_threshold float DEFAULT 0.7, p_limit int DEFAULT 5)` returning matching chunks ranked by cosine similarity
- Add an FastAPI helper `retrieve_for_query(tenant_id, query_text)` that embeds the query and calls the SQL function
- Cache query embeddings in Upstash Redis with 5-minute TTL (same exact query = no re-embed)

**Acceptance criteria**:

- Retrieval returns 0–5 chunks based on relevance (threshold respected)
- Tenant A querying never returns tenant B's chunks (RLS verified)
- Helper round-trip under 200ms p95 (cache miss) or under 20ms (cache hit)
- 0.7 threshold tuned to avoid hallucination-prone irrelevant retrievals

**Dependencies**: 4.03, 4.04

**Estimate**: 3h

---

## 4.06 — RAG injection in the pipeline

**Description**: Wire the retrieval helper into the LLM step of the Pipecat pipeline so the agent can answer from the tenant's knowledge.

**Tasks**:

- In `make_pipeline`, wrap the LLM provider with a retrieval step
- On each user turn, embed the latest utterance, call `retrieve_knowledge`
- If chunks come back above the threshold, prepend them to the LLM context as a `KNOWLEDGE` system message block
- Format: `Use the following information from the business when answering: <chunks>. If the answer is not in this context, say you don't know and offer to transfer the call.`
- Track retrieval metrics per turn: chunks_returned, top_similarity, retrieval_ms
- Persist retrieval metrics on `call_messages` in a `retrieval_meta` JSONB column

**Acceptance criteria**:

- A test call to a tenant with an uploaded menu PDF answers menu questions correctly
- A test call to the same tenant with off-topic questions falls back to "I don't know" (does not hallucinate)
- Retrieval adds under 200ms p95 to the per-turn loop (cache hit path under 20ms)
- `retrieval_meta` captures chunks_returned, top_similarity, retrieval_ms on every assistant turn
- Total per-turn latency budget still met (under 1.2s p90)

**Dependencies**: 3.10, 4.05

**Estimate**: 4h

---

## 4.07 — Tool registry framework

**Description**: Build the framework that defines, registers, and dispatches tools the LLM can call.

**Tasks**:

- Create `tools/` package with a base `Tool` class: `name`, `description`, `parameters_schema` (Pydantic), `execute(tenant, agent, call, args)`
- Implement a `ToolRegistry` that maps tool names to classes
- Wire the registry into the LLM provider: at pipeline construction, expose only tools in the agent's `tool_whitelist` to the LLM
- Generate OpenAI-compatible tool schemas from the Pydantic models for DeepSeek's tool-calling format
- Add a dispatcher that runs `execute()` when the LLM emits a tool call, surfaces results back into the conversation context, and logs the call to `call_messages` with role `tool`

**Acceptance criteria**:

- Adding a new tool is a single-class change plus a registry entry
- Whitelist enforcement: a tool not in the agent's whitelist never appears in the LLM's tool list
- Tool execution errors surface to the LLM as `{"error": "<message>"}` so the agent can apologize and recover
- `call_messages` shows tool calls with role=`tool`, content=`<args + result>`, latency_ms

**Dependencies**: 3.10

**Estimate**: 3h

---

## 4.08 — transferToHuman tool

**Description**: First tool. Transfers the call to a human number configured on the agent.

**Tasks**:

- Add `transfer_to_number` column to `agents` table (E.164 format)
- Implement `TransferToHuman` tool: `parameters_schema` is `{reason: str}` (optional)
- `execute()` emits a Pipecat command that issues a Twilio `<Dial>` TwiML to redirect the call
- Play a short bridge message ("Connecting you to a team member, one moment") via TTS before the transfer
- Record the transfer event on `call_messages` and update `calls.ended_reason = 'transferred'`
- Handle the case where the transfer number is missing or invalid (graceful error to LLM)

**Acceptance criteria**:

- LLM can call `transferToHuman` and the call actually rings the configured number
- Bridge message plays before the transfer
- Transfer event captured in `call_messages` and `calls`
- If `transfer_to_number` is null, tool returns an error and LLM apologizes
- End-to-end test: caller asks for a human, gets transferred, hears the team

**Dependencies**: 4.07

**Estimate**: 3h

---

## 4.09 — sendSms tool

**Description**: Send an SMS to the caller (or a number derived from the conversation) via the Twilio API.

**Tasks**:

- Implement `SendSms` tool: `parameters_schema` is `{to: str (E.164), body: str (max 320 chars)}`
- `execute()` sends via Twilio Messaging API using the tenant's number as `from`
- Default `to` to the caller's number when the LLM doesn't supply one
- Validate `body` length and reject if it would exceed Twilio's 1600-char hard cap
- Log the SMS event on `call_messages` and a new `sms_log` table (id, tenant_id, call_id, to, body, twilio_sid, status, error)
- Handle Twilio errors gracefully (returns to LLM as a structured error)

**Acceptance criteria**:

- LLM can send an SMS to the caller's number during the call
- SMS appears in `sms_log` with Twilio SID
- Twilio delivery status (delivered / failed) backfilled via a status webhook
- LLM-supplied long body gets truncated cleanly at 320 chars (with "…" marker)
- Cross-tenant: tenant A's agent cannot send from tenant B's number (enforced by `from = tenant.phone_number`)

**Dependencies**: 2.01, 4.07

**Estimate**: 3h

---

## 4.10 — escalateToOwner tool

**Description**: Notify the tenant's owner (configured contact) about a call that needs their attention, with a one-line summary.

**Tasks**:

- Add `escalation_email` and `escalation_sms` columns to `tenants` (either or both can be set)
- Implement `EscalateToOwner` tool: `parameters_schema` is `{summary: str (max 200 chars), urgency: enum(low|medium|high)}`
- `execute()` sends an email via Resend and/or an SMS via Twilio depending on tenant config
- Email includes: tenant name, call ID, caller number, summary, urgency, link to the call detail page
- Log on `call_messages` and on a new `escalations` table
- Don't block the call — escalation is fire-and-forget from the agent's POV

**Acceptance criteria**:

- Owner receives email/SMS within 30s of the LLM calling the tool
- Email links land on the right call detail page (Phase 5 routes)
- Failures don't crash the call — agent says "I've passed this to the team" regardless
- Urgency translates to email subject prefix (`[URGENT]`, `[HIGH]`, etc.)
- Escalation row captures the full payload for the audit trail

**Dependencies**: 4.07

**Estimate**: 3h

---

## 4.11 — Tool whitelisting and Pydantic validation

**Description**: Lock down which tools each agent can call and validate all tool arguments before dispatch.

**Tasks**:

- Confirm `agents.tool_whitelist` is a text[] column; populate the multi-select in 3.08 with the three v1 tools
- At `make_pipeline`, filter the registry to only whitelisted tools before exposing schemas to the LLM
- Run Pydantic validation on every incoming tool call's arguments; on validation failure, return the error to the LLM so it can retry
- Add a sanity check that whitelisted tool names exist in the registry (catches typos at agent save time, validated in 3.07 PATCH)
- Log every tool dispatch with the resolved args (after validation) and the result size

**Acceptance criteria**:

- Calling a non-whitelisted tool is impossible — it doesn't appear in the LLM's tool list
- Invalid arguments (wrong types, missing required fields) return a clear error the LLM can recover from
- Agent save form (3.08) rejects unknown tool names
- Every tool dispatch shows up in logs and `call_messages` with full args

**Dependencies**: 3.07, 3.08, 4.07, 4.08, 4.09, 4.10

**Estimate**: 2h

---

## 4.12 — Per-tool rate limits and idempotency keys

**Description**: Prevent runaway tool spam and accidental duplicate side effects.

**Tasks**:

- Implement Upstash Redis rate limits per tool per call: `transferToHuman` max 1/call, `sendSms` max 3/call, `escalateToOwner` max 2/call
- On rate-limit hit, return a structured error to the LLM ("This tool has been used the maximum number of times this call")
- Add an idempotency key (UUID generated per LLM tool-call attempt) so re-tries of the same call don't double-execute
- Idempotency cached for 10 minutes in Redis
- Add unit tests for the rate limit + idempotency logic

**Acceptance criteria**:

- LLM that tries to call `sendSms` 5 times only sends 3 SMSes
- The same idempotency key returns the cached result instead of re-executing
- Rate limit resets between calls (per-call scope, not per-tenant)
- Errors readable to the LLM (no opaque 429s in the conversation context)

**Dependencies**: 4.07, 4.08, 4.09, 4.10

**Estimate**: 2h

---

## 4.13 — Post-call summary job

**Description**: After every call ends, generate a one-paragraph summary, an intent classification, and an outcome label; write to `calls`.

**Tasks**:

- Add columns to `calls`: `summary` (text), `intent` (text), `outcome` (enum: resolved, transferred, escalated, abandoned, other), `summary_generated_at`
- Background job triggered on Twilio status callback "completed"
- Job reads the call's `call_messages`, builds a prompt for DeepSeek V4 Flash, parses a JSON response
- Use a stable system prompt so DeepSeek caches the prefix (cheaper)
- Retry once on failure; on persistent failure, write `summary = null` and `intent = 'unclassified'`
- Surface summary + intent in the Phase 5 portal call detail view

**Acceptance criteria**:

- Every completed call has a summary within 60s of `ended_at`
- Summary is under 80 words and grounded in the actual transcript (not hallucinated)
- Intent classification consistent across re-runs for the same transcript (low temperature)
- Outcome labels accurate on a hand-checked sample of 20 test calls
- Job is idempotent — re-running on the same call replaces, doesn't append

**Dependencies**: 2.13, 2.19

**Estimate**: 3h

---

## 4.14 — Cost calculation per call

**Description**: Compute and persist the actual COGS for each call from `provider_snapshot`, duration, and per-turn `tts_chars`.

**Tasks**:

- Add columns to `calls`: `cost_stt_usd`, `cost_tts_usd`, `cost_llm_usd`, `cost_telephony_usd`, `cost_total_usd`
- Build a `cost_calculator.py` module with provider-specific formulas:
  - Deepgram STT Nova-3 Monolingual: `duration_secs / 60 * 0.0048`
  - Deepgram TTS Aura-1: `sum(call_messages.tts_chars) / 1000 * 0.015`
  - DeepSeek V4 Flash: sum of input/output tokens × published rates (separate cached vs uncached)
  - Twilio India: `duration_secs / 60 * 0.0085` (inbound) — adjust if Twilio rates change
- Run the calculator at post-call summary time (same job as 4.13)
- Show per-call cost in the internal call detail view
- Aggregate to per-tenant per-day for the billing job in Phase 5

**Acceptance criteria**:

- Cost columns populated within 60s of `ended_at`
- Calculator matches actual Deepgram and DeepSeek invoices within ±5% on a 100-call sample
- TTS cost is per-character (not per-minute) — verified against the `tts_chars` sum
- Tenants using different `provider_config` get the right formula automatically
- Internal call detail shows the four-component cost breakdown

**Dependencies**: 2.13, 2.15, 4.13

**Estimate**: 3h

---

## 4.15 — Knowledge browser in dashboard

**Description**: Add the Knowledge tab to the internal tenant detail page so internal staff can upload, inspect, retry, and delete documents.

**Tasks**:

- Build the Knowledge tab in `/internal/tenants/{id}?tab=knowledge`
- File upload widget (drag-and-drop, PDF only, max 20MB) wired to 4.01
- List view: filename, uploaded date, status (pending / processing / ready / error), chunk count
- Status badge auto-refreshes every 5s while a doc is processing
- Detail drawer: filename, full error if status=error, sample chunks (first 3 with content + similarity preview)
- Reprocess button and delete button (with confirmation modal)

**Acceptance criteria**:

- Upload to ready state visible in the UI without page refresh
- Failed docs show the error message and offer reprocess
- Sample chunks readable so internal staff can sanity-check ingestion quality
- Delete cascades to embeddings + Storage file (verified)
- Audit log shows every action

**Dependencies**: 4.01, 4.02, 4.03

**Estimate**: 3h

---

## 4.16 — Phase 4 complete testing

**Description**: End-to-end testing of knowledge retrieval, tool calling, summaries, and cost calculation before moving to Phase 5.

**Tasks**:

- Upload a realistic 20-page menu PDF for a test tenant
- Verify ingestion completes and chunks look right
- Make 10 test calls covering: menu questions (RAG path), transfer request (tool path), SMS request (tool path), escalation (tool path), and one purely conversational call
- Verify each tool fires exactly once per request (no duplicates)
- Verify summaries make sense on all 10 calls
- Verify cost columns match a manual calculation from `provider_snapshot` + transcripts
- Verify a tenant with no knowledge doc still works (RAG returns nothing, agent says "I don't know")
- Verify cross-tenant: tenant A's RAG never returns tenant B's chunks
- Check Deepgram dashboard consumption matches the test-call duration ± 10%

**Acceptance criteria**:

- 10 test calls succeed with the right tools called
- Summaries readable and accurate
- Costs match manual calc within ±5%
- No cross-tenant data leakage
- No P0 bugs open
- Deepgram credit usage matches expected to within 10%

**Dependencies**: 4.06, 4.08, 4.09, 4.10, 4.11, 4.13, 4.14, 4.15

**Estimate**: 4h

---

# Phase 5 — Client portal, billing, and compliance

Onboarding-readiness week. Tenants can see their own data in the read-only portal. Onboarding is **sales-led**: prospects reach us through landing-page CTAs, we agree a plan and take payment over email, then the team provisions the tenant and issues a login valid for the paid period (`paid_until`). **No payment gateway in v1** — payments are offline and recorded manually; a real gateway (e.g. Razorpay/Cashfree) is deferred. **Paid-only — there is no free trial**; access begins after payment. DPDP export/delete endpoints work. Sentry catches errors with PII scrubbed.

---

## 5.01 — Pricing plans (config, no payment gateway)

**Description**: Define the v1 India English plans in the backend for display and as the reference the team uses when invoicing manually. No payment gateway.

**Tasks**:

- Migration for `pricing_plans`: `id`, `key` (`starter` | `pro`), `name`, `price_inr_month`, `included_minutes`, `overage_inr_per_min`, `active`, `created_at`
- Seed:
  - Starter: ₹2,999/month, 300 min/month, ₹15/min overage
  - Pro: ₹7,999/month, 1000 min/month, ₹12/min overage
- Read API for the marketing pricing page + internal onboarding use
- GST (18%) noted for manual invoices — no automated tax

**Acceptance criteria**:

- `pricing_plans` seeded and queryable
- Marketing pricing page + internal onboarding read the same source
- Plans editable via migration/seed without code changes

**Dependencies**: None (can start in parallel)

**Estimate**: 1.5h

---

## 5.02 — Lead capture from landing CTAs

**Description**: Landing-page CTAs ("Get started", "Book a demo", "Contact sales") open a dialog that captures the prospect and notifies the team by email — the entry point of the sales-led onboarding. No free trial — v1 is paid-only.

**Tasks**:

- Migration for `leads`: `id`, `business_name`, `contact_name`, `contact_email`, `contact_phone`, `message`, `source` (which CTA), `status` (`new` | `contacted` | `converted` | `lost`), `created_at`
- Public `POST /leads` endpoint (rate-limited, no auth): validate + store the lead, send a notification email to the team inbox via Resend (4.10)
- Marketing: CTA buttons open a lead dialog (name, business, email, phone, optional message) → submit → success state ("We'll email you shortly")
- Update landing-page copy + CTAs to the paid-only, sales-led model: **remove all "free trial" / "no credit card" / "7-day free trial" messaging** (hero, pricing/FAQ, footer CTA, SEO meta); CTAs read "Get started" / "Book a demo" / "Contact sales" and open the lead dialog
- Internal "Leads" inbox page: list + status update (new → contacted → converted / lost)

**Acceptance criteria**:

- Submitting the dialog stores a `leads` row and emails the team within 60s
- Spam/abuse mitigated (rate limit + basic validation)
- Internal staff can see and triage leads
- No public self-serve tenant creation happens from the landing page
- No "free trial" / "no credit card" messaging remains anywhere on the marketing site (paid-only)

**Dependencies**: 4.10

**Estimate**: 3h

---

## 5.03 — Tenant access window + expiry enforcement

**Description**: Access is time-bound to what the client paid for. A `paid_until` date governs whether a tenant's agents answer calls.

**Tasks**:

- Add `paid_until timestamptz` to `tenants`
- Scheduled job: pause (set `status = 'paused'`) any active tenant whose `paid_until` has passed; log to audit (system actor)
- Call routing already gates on `status = 'active'`, so paused tenants stop answering immediately
- Internal UI: set / extend `paid_until` on a tenant (audited)
- Optional: warn the team N days before expiry

**Acceptance criteria**:

- A tenant past `paid_until` stops taking calls within the job interval
- Extending `paid_until` re-activates the tenant
- Per-call scope unaffected — this is per-tenant access, not per-call
- Every change to `paid_until` is audited

**Dependencies**: 3.09, 3.11

**Estimate**: 3h

---

## 5.04 — Manual onboarding + client login provisioning

**Description**: After the team agrees a plan and receives payment over email, they provision the tenant and hand the client a login valid for the paid period.

**Tasks**:

- Reuse tenant provisioning (3.06): create tenant + agent + number
- Create the client's portal login: a `tenant_users` row linked to a Supabase auth user (invite / set password / magic link)
- Set `paid_until` (5.03) to the paid-through date
- Send a welcome email (Resend) with the portal URL + login instructions
- Mark the originating lead `converted` (5.02)
- **Disable public self-serve signup** (modifies Phase 1): landing CTAs point to the lead dialog, not `/signup`; gate the 1.09 `handle_new_user` auto-tenant trigger so tenants are created only by the team — no public self-serve tenant creation

**Acceptance criteria**:

- Team can take a lead from "paid" to "client logged into the portal" without self-serve checkout
- Client login only sees their own tenant (RLS)
- Welcome email lands within 60s with a working portal link
- `paid_until` reflects the paid period
- No public visitor can self-create a tenant (signup is team-driven only in v1)

**Dependencies**: 3.06, 5.02, 5.03

**Estimate**: 3h

---

## 5.05 — Record a payment (manual) + extend access

**Description**: Record an offline payment (UPI / bank transfer / etc.) so access and billing history stay accurate. Replaces automated gateway webhooks.

**Tasks**:

- Internal "Record payment" action on a tenant: `amount_inr`, `method`, `plan`, `period_start`, `period_end`, `reference` (UTR / note)
- Sets / extends `tenants.paid_until` to `period_end` (5.03)
- Writes a `billing_events` row (`event_type = 'payment_recorded'`)
- Audited via 3.11

**Acceptance criteria**:

- Recording a payment extends `paid_until` and writes exactly one `billing_events` row
- Internal billing view shows payment history per tenant
- No card / payment-instrument data stored — only an offline payment reference
- Recording a payment for an expired tenant re-activates it (via 5.03)

**Dependencies**: 5.03, 5.07

**Estimate**: 2h

---

## 5.06 — Usage aggregation (provider-agnostic)

**Description**: Daily rollup of each tenant's minutes + cost from `calls`, for the portal usage card and the team's manual invoicing. No external usage push.

**Tasks**:

- Scheduled job at 00:30 IST daily
- For each active tenant: sum `duration_secs / 60` and `cost_total_usd` for the previous day's calls
- Compute cycle-to-date minutes vs the plan's included minutes (overage minutes, for manual invoicing)
- Write a `billing_events` row (`event_type = 'usage_reported'`) per tenant per day
- Idempotent: re-running for the same day replaces, doesn't append

**Acceptance criteria**:

- After 10 test calls totaling 80 minutes for a Starter tenant (300 included), 0 overage minutes recorded
- After 350 minutes total, 50 overage minutes recorded for invoicing
- Re-running the job for the same day doesn't double-count
- Usage card + manual invoice read the same numbers
- Job runs in under 5 minutes for 1000 tenants

**Dependencies**: 4.14

**Estimate**: 3h

---

## 5.07 — billing_events table writes

**Description**: Define and populate the `billing_events` audit-style log that powers the portal billing page and internal billing dashboards.

**Tasks**:

- Migration for `billing_events`: `id`, `tenant_id`, `event_type` (`payment_recorded`, `usage_reported`, `access_extended`, `plan_changed`), `amount_inr` (nullable), `metadata_json`, `created_at`
- Write helper used by 5.05 (record payment) and 5.06 (usage aggregation)
- Add tenant-scoped read API: `GET /api/billing/events` for the portal billing page
- Internal-scoped read API: `GET /internal/tenants/{tid}/billing` for staff troubleshooting

**Acceptance criteria**:

- Every recorded payment and every daily usage report writes exactly one row
- Tenant API returns only their own events (RLS-enforced)
- Internal API returns any tenant's events
- Schema is queryable for monthly revenue / MRR rollups
- No payment-instrument data ever stored in `metadata_json` (offline reference only)

**Dependencies**: 5.05, 5.06

**Estimate**: 2h

---

## 5.08 — Portal dashboard page

**Description**: Replace the Phase 1 placeholder `/portal` dashboard with the real overview a tenant sees on login.

**Tasks**:

- Hero stats: calls this month, minutes used / minutes included, escalations this month
- Calls-over-time chart (last 14 days)
- "Recent calls" list (5 most recent, click → call detail)
- "Knowledge status" card (X documents, last upload date)
- "Plan" card (current plan, access valid until `paid_until`, "Contact us to renew" — no self-serve)
- Empty states for tenants with no calls / no knowledge yet

**Acceptance criteria**:

- Loads under 1s for tenants with up to 10k calls
- Numbers match `calls` table aggregation exactly
- Charts render correctly on mobile
- All click-throughs work (recent calls → detail, manage plan → portal)
- Skeleton loading state, no flash of empty data

**Dependencies**: 1.15, 4.14, 5.07

**Estimate**: 4h

---

## 5.09 — Portal calls list page

**Description**: Build the tenant-facing call history page.

**Tasks**:

- Paginated list, newest first, default 25 per page
- Columns: started at, caller number (masked: +91 XXXXX X1234), duration, outcome, intent, summary preview (first 100 chars)
- Filter chips: outcome, intent, date range
- Search by caller number (full-text) and summary content
- Click row → call detail page (5.10)
- Export current view as CSV (tenant-friendly columns only, no internal cost fields)

**Acceptance criteria**:

- All columns populated from Phase 4 data
- Caller number masking applied client-side (full number still in DB for compliance)
- CSV export downloads correctly
- Pagination smooth, search debounced
- Empty state for tenants with no calls yet

**Dependencies**: 4.13, 5.08

**Estimate**: 3h

---

## 5.10 — Portal call detail page

**Description**: Build the per-call detail view for tenants — transcript, audio player, summary, escalations, tools called.

**Tasks**:

- Header: call ID, started/ended timestamps, duration, caller number (masked), agent name
- Summary card with intent and outcome badges
- Audio player with playback controls (signed URL from Storage, 1-hour expiry)
- Transcript: timeline of `call_messages`, role-labeled, with timestamps
- Tools-called section: list of tool dispatches with args (PII scrubbed for sendSms)
- Escalation card if this call escalated to the owner (with the owner-summary text)
- "Download transcript" button → text file

**Acceptance criteria**:

- Audio plays inline in the browser
- Transcript renders correctly for calls with 50+ turns
- Signed URL refreshes if a tenant reloads after >1h
- Tool args scrubbed of PII (no full phone numbers in displayed args)
- Cross-tenant: tenant A cannot access tenant B's call detail (RLS enforced server-side, plus URL guard)

**Dependencies**: 2.14, 5.09

**Estimate**: 4h

---

## 5.11 — Portal billing page

**Description**: Build the read-only billing page where tenants see their plan, usage, payment history, and access window. No self-serve payment in v1.

**Tasks**:

- Plan card: current plan, included minutes, **access valid until `paid_until`**, "Contact us to renew" (mailto / lead form — no checkout)
- Usage card: minutes used this cycle, projected end-of-cycle minutes, overage minutes so far (from 5.06)
- Payment history list: recorded payments + daily usage rollups from `billing_events`
- Expiry banner: warns when `paid_until` is near or past (read-only, points to renewal contact)

**Acceptance criteria**:

- All data sources from `billing_events`, `tenants.paid_until`, and the usage rollup
- Tenants near/after expiry see a clear banner with how to renew
- No payment-collection UI (no checkout, no card entry) in v1
- Cross-tenant: a tenant only sees their own billing data (RLS)

**Dependencies**: 5.03, 5.06, 5.07

**Estimate**: 3h

---

## 5.12 — DPDP export endpoint

**Description**: Build the DPDP-compliant data export endpoint that lets a tenant download all their data.

**Tasks**:

- `POST /api/dpdp/export` — kicks off a background job
- Background job collects: tenant row, all users, all agents, all calls (with messages), all knowledge docs (metadata + content), all billing events, full audit log scoped to this tenant
- Package as a ZIP with one JSON file per table + the original PDF files
- Upload to Storage `exports/{tenant_id}/{export_id}.zip`
- Email the tenant a signed download link with 7-day expiry via Resend
- Audit-log the export request and the email send

**Acceptance criteria**:

- Tenant can trigger export from `/portal/settings`
- Email arrives within 5 minutes for a tenant with 1000 calls
- ZIP contains all expected data (verified on a test tenant)
- Download link works for 7 days, then 404
- Re-triggering an export creates a new ZIP (doesn't overwrite — audit trail)
- No PII for other tenants leaks (verified by inspecting a multi-tenant test)

**Dependencies**: 4.15

**Estimate**: 3h

---

## 5.13 — DPDP delete endpoint

**Description**: Build the DPDP-compliant data deletion endpoint.

**Tasks**:

- `POST /api/dpdp/delete` — requires a confirmation token sent to the tenant's email first
- Background job:
  - Soft-deletes the tenant (sets `deleted_at`) so audit trail survives
  - Hard-deletes `call_messages`, `knowledge_embeddings`, Storage files (recordings + knowledge PDFs)
  - Stops billing access (clears `paid_until`, marks the tenant churned)
  - Removes Twilio webhook config from purchased numbers (number itself can be released or retained per policy)
  - Anonymizes residual records (caller numbers in `calls` → null after the audit window)
- Email the tenant when deletion is complete
- Internal flag prevents accidental triggering for active paying tenants without explicit confirmation

**Acceptance criteria**:

- Tenant can request deletion from `/portal/settings`
- Confirmation email arrives, click-through triggers actual deletion
- All call recordings + knowledge files removed from Storage (verified)
- Billing access stopped (`paid_until` cleared, tenant churned)
- Audit log retains the deletion event (the audit row itself survives)
- Re-signup with the same email creates a brand new tenant (no zombie data)

**Dependencies**: 5.12

**Estimate**: 3h

---

## 5.14 — Consent compliance check + per-tenant override

**Description**: Confirm the Phase 2 pre-call consent disclosure (2.17) meets DPDP requirements and let tenants in different markets override the disclosure text.

**Tasks**:

- Review the 2.17 disclosure wording with a quick legal sanity-check against DPDP §6 (notice of processing)
- Add `consent_disclosure_text` column to `tenants` (nullable; defaults to the standard line)
- Update the Twilio voice webhook to use the tenant's override if set
- Add a settings page entry (read-only for v1, editable for v1.5+) showing the current disclosure
- Add a test that the disclosure plays before any audio capture starts (i.e. consent precedes recording)

**Acceptance criteria**:

- Standard disclosure passes a DPDP sanity-check (no legal pre-clearance in v1, but documented for v1.5 review)
- Per-tenant override works end-to-end
- Recording verifiably starts AFTER the disclosure plays (no pre-roll capture)
- Settings page shows the active disclosure text

**Dependencies**: 2.17

**Estimate**: 2h

---

## 5.15 — 30-day recording retention job

**Description**: Daily job that deletes call recordings older than 30 days from Supabase Storage to honor the v1 retention policy.

**Tasks**:

- Scheduled job at 03:00 IST daily
- Query `calls` where `recording_url IS NOT NULL` and `ended_at < now() - interval '30 days'`
- Delete the Storage file
- Set `recording_url = null` and `recording_deleted_at = now()` on the row
- Keep the transcript (`call_messages`) — only audio is purged
- Tenant-specific override possible later (some plans may want 90 days); for v1 it's a global 30
- Audit log each deletion batch

**Acceptance criteria**:

- 31-day-old recordings deleted on the next run
- 29-day-old recordings retained
- `recording_url` nulled on the affected rows
- Transcripts still readable in the portal after audio is gone (UI shows "Recording expired")
- Job is idempotent — re-running doesn't error on already-deleted files

**Dependencies**: 2.14

**Estimate**: 2h

---

## 5.16 — Sentry frontend integration

**Description**: Install Sentry for the Next.js app and capture user-facing errors with PII scrubbed.

**Tasks**:

- Install `@sentry/nextjs`
- Configure DSN via env var
- Set sample rates: 100% for errors, 10% for performance traces
- Tag every event with `tenant_id` (when available) and `user_id` (hashed, not raw email)
- Configure `beforeSend` to strip cookies, auth headers, and known PII fields
- Add source maps upload to CI
- Set release tag from the Vercel deployment SHA

**Acceptance criteria**:

- A thrown error in the portal lands in Sentry within 30s
- The error has `tenant_id` and a hashed `user_id`
- No raw email, phone, or auth token visible in any captured event
- Source maps resolved correctly (real stack traces, not minified)
- Release tag matches the deployed commit

**Dependencies**: 1.18

**Estimate**: 2h

---

## 5.17 — Sentry backend integration

**Description**: Install Sentry for the FastAPI app and capture backend errors with the same PII discipline.

**Tasks**:

- Install `sentry-sdk[fastapi]`
- Configure DSN via env var
- Set sample rates: 100% errors, 5% performance traces
- Tag events with `tenant_id`, `call_id`, `request_id`
- Configure `before_send` to strip caller phone numbers, auth tokens, full PDF content, embeddings
- Hook in to FastAPI middleware so every uncaught exception surfaces
- Set release tag from the Render deployment SHA

**Acceptance criteria**:

- A backend exception lands in Sentry within 30s
- Provider errors (Deepgram timeout, DeepSeek 429) caught with the right context
- No PII visible (caller numbers null, embeddings stripped)
- Performance traces show p50/p95 per endpoint
- Source location maps to the right repo commit

**Dependencies**: 1.17

**Estimate**: 2h

---

## 5.18 — PII scrubbing helper (beforeSend pipeline)

**Description**: Centralize the PII scrubbing logic used by 5.16 and 5.17 into a shared module.

**Tasks**:

- Build a `pii_scrub.py` (backend) and `piiScrub.ts` (frontend) with identical rules
- Rules: redact phone numbers (E.164 and Indian formats), emails (except `@yourdomain.ai`), Aadhaar-shaped IDs, PAN-shaped IDs, full names matched against a small known-customer list, credit card numbers (Luhn-passing 13–16 digit strings)
- Replace matches with placeholder tokens (`[PHONE]`, `[EMAIL]`, etc.) so the structure of errors is still debuggable
- Wire into `beforeSend` for both Sentry SDKs
- Unit test with sample dirty payloads to verify nothing leaks

**Acceptance criteria**:

- Test fixtures with phones, emails, Aadhaar, PAN, cards all get redacted
- Whitelisted internal emails (`@yourdomain.ai`) NOT redacted (so we can debug our own staff)
- Both frontend and backend use the same rules (verified via shared test fixtures)
- Performance: scrubbing adds under 5ms to event submission

**Dependencies**: 5.16, 5.17

**Estimate**: 3h

---

## 5.19 — First-cohort onboarding workflow

**Description**: Document and tool the manual onboarding flow for the first 3-5 paying tenants (clinics or restaurants in Delhi).

**Tasks**:

- Write a runbook in `/docs/onboarding.md`: prospect call → demo → tenant creation (3.06) → number purchase → agent prompt drafting → KB upload → smoke call → go live
- Build an "Onboarding Checklist" page in the internal dashboard with checkboxes synced to a `tenant_onboarding` table (one row per tenant: prompt_drafted, kb_uploaded, smoke_call_passed, escalation_configured, payment_recorded, gone_live, gone_live_at)
- Add a per-tenant note field (markdown) so internal staff can leave context
- Add a "Go live" button that flips tenant status to `active` and confirms `paid_until` is set (5.03/5.05)
- Send the tenant a welcome email via Resend after "Go live"

**Acceptance criteria**:

- Runbook readable end-to-end in under 10 minutes
- Checklist persists state across internal staff sessions
- "Go live" only enables when all required checkboxes are ticked (including payment recorded)
- Welcome email lands within 60s, with the portal login link
- First test tenant onboarded fully through this workflow

**Dependencies**: 3.05, 3.06, 4.15, 5.04, 5.05

**Estimate**: 3h

---

## 5.20 — Phase 5 complete testing

**Description**: End-to-end testing of the portal, billing, compliance, and onboarding flow before declaring v1 MVP done.

**Tasks**:

- Submit the landing lead form → verify a `leads` row + team notification email (5.02)
- Onboard a fake "Restaurant X" tenant fully through 5.19 (the checklist + runbook): provision + login + `paid_until` set (5.04/5.05)
- Tenant logs into the portal — verify dashboard, calls list, call detail, billing page all render
- Generate 350 minutes of test calls → daily usage aggregation (5.06) records 50 overage minutes for invoicing
- Let `paid_until` lapse → expiry job pauses the tenant (agents stop); record a payment (5.05) → tenant re-activates
- Tenant requests data export — receives the email, downloads ZIP, verifies contents
- Tenant requests deletion — verifies all data wiped, billing access stopped (`paid_until` cleared, churned), audit trail intact
- Trigger a frontend error and a backend error — verify Sentry capture with PII scrubbed
- Run the 30-day retention job against a seeded old call — verifies audio deletion + transcript retention
- Run the cross-tenant smoke test from 1.05 one more time end-to-end
- Compute total Phase 5 Deepgram + Twilio + DeepSeek + OpenAI cost from the test run and confirm against `cost_total_usd` aggregation

**Acceptance criteria**:

- End-to-end onboarding works in under 30 minutes for a new tenant
- Portal pages all load under 1s
- Manual onboarding + access window (`paid_until` expiry/renewal) + usage aggregation work correctly
- DPDP export + delete both verified
- Sentry captures errors with no PII leakage
- 30-day retention deletes only the right files
- Cost calculator matches measured spend within ±5%
- No P0 bugs open
- Phase 5 — and the v1 MVP — declared shippable

**Dependencies**: 5.08, 5.09, 5.10, 5.11, 5.12, 5.13, 5.15, 5.16, 5.17, 5.18, 5.19

**Estimate**: 5h

---

_End of tickets.md_
