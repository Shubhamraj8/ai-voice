# MVP planning

Execution plan for v1. Five phases, one phase per week, with a sixth week reserved for buffer and customer onboarding.

This document defines what gets built each week, the technical approach for each component, and the milestone that marks each phase complete. Companion to `design.md` (architecture), `features.md` (full inventory), and `roadmap.md` (post-v1 phases).

---

## Contents

1. [Phase overview](#phase-overview)
2. [Pre-phase setup](#pre-phase-setup)
3. [Phase 1 — Foundation](#phase-1--foundation)
4. [Phase 2 — Voice pipeline](#phase-2--voice-pipeline)
5. [Phase 3 — Internal dashboard + multi-tenancy](#phase-3--internal-dashboard--multi-tenancy)
6. [Phase 4 — Business brain](#phase-4--business-brain)
7. [Phase 5 — Client portal + billing](#phase-5--client-portal--billing)
8. [Week 6 — Buffer and customers](#week-6--buffer-and-customers)
9. [Ordering rationale](#ordering-rationale)

---

## Phase overview

| Phase | Week | Focus | Milestone |
|---|---|---|---|
| 1 | 1 | Foundation | Both apps deployed, auth working, schema and RLS in place |
| 2 | 2 | Voice pipeline | First end-to-end AI call works from a real phone |
| 3 | 3 | Internal dashboard + multi-tenancy | Team configures tenants via dashboard, calls route per tenant |
| 4 | 4 | Business brain | RAG live, tools live, agents answer knowledge-base questions and take actions |
| 5 | 5 | Client portal + billing | Stripe live, read-only portal live, first customers onboarded |
| 6 | 6 | Buffer | Stabilization, additional customers, demo content |

---

## Pre-phase setup

Done over a weekend before Phase 1 begins. Not counted in the five weeks.

### Accounts and verification

- Vercel, Render, Supabase, Upstash, Sentry, Resend
- Stripe in live mode with India payment methods enabled (UPI, RuPay, NetBanking)
- Twilio account with India local number provisioning (verification can take 1–2 business days)
- Cartesia, Inworld, DeepSeek (each provides starter credits sufficient for the development phase)
- GitHub organization and team access

### Domain and DNS

- Domain registered
- DNS pointed at Vercel for apex, `www`, and `app` subdomain
- `api` subdomain pointed at Render service
- TLS certificates verified for all subdomains

### Repository

Monorepo structure:

```
/apps
  /web                # Next.js frontend
  /api                # FastAPI backend
/packages
  /db                 # Postgres migrations and shared types
  /shared             # Shared TypeScript types and zod schemas
/docs                 # design.md, mvp-planning.md, features.md, roadmap.md
```

### Local development

- `pnpm dev` runs Next.js with hot reload
- `uvicorn app.main:app --reload` runs FastAPI
- Both connect to a shared Supabase development project
- Pre-commit hooks for lint, typecheck, and format

### CI / CD

- GitHub Actions on every PR: lint, typecheck, run tests
- Vercel auto-deploys frontend previews on PR
- Render auto-deploys backend from `main` after CI passes

---

## Phase 1 — Foundation

**Week 1.** Both apps deployed and authenticated. Database schema and Row Level Security in place.

This phase establishes everything else. By end of week, a new user can sign up, log in, and reach an empty client portal. The schema is in place such that subsequent phases only add data and behavior, not structural changes.

### Frontend

- Next.js 14 with App Router, TypeScript strict mode, Tailwind CSS, shadcn/ui
- Route group structure:
  - `(marketing)` — landing page, pricing page
  - `(internal)` — internal dashboard, protected by internal-user role
  - `(portal)` — client portal, protected by tenant-user role
- Supabase Auth integration via `@supabase/ssr` with email + password
- Sign up flow that creates an `auth.users` row and a corresponding `tenants` row
- Login page, signup page, password reset page
- Route guards: unauthenticated users on `/portal` or `/internal` redirect to `/login`
- Empty client portal shell with navigation and layout
- Vercel deployment with auto-deploy from `main`

### Backend

- FastAPI application with structured layout (`/routes`, `/models`, `/providers`, `/db`, `/services`)
- asyncpg connection pool to Supabase Postgres with retry logic on transient errors
- Pydantic v2 models for `Tenant`, `User`, `Agent`, `Call`
- Supabase service-role client for trusted backend writes that bypass RLS
- JWT verification middleware that extracts the authenticated user from the Supabase token
- `/health` endpoint for warm-ping cron
- `/me` endpoint returning the authenticated user with their tenant context
- Render deployment with auto-deploy from `main`
- External cron (cron-job.org) configured to hit `/health` every 10 minutes
- Structured logging via structlog

### Database

Migrations create the core tables per `design.md` §6–7:

- `tenants` — business name, market, language, timezone, plan, provider_config (JSONB), onboarding_mode
- `tenant_users` — many-to-many link between Supabase users and tenants with role (owner / admin / member)
- `internal_users` — internal team members with role (admin / sales / support)
- `agents` — name, system_prompt, tools array, voice_id, phone_number, twilio_sid, version
- `calls` — references to tenant and agent, twilio_call_sid, timing, duration, recording_url, summary, outcome, cost_usd, provider_snapshot
- `call_messages` — per-turn transcript with role, content, tool data, latency
- `audit_log` — actor, action, payload, timestamp

### Row Level Security

Policies applied to every tenant-scoped table:

- Authenticated tenant users can only see rows where `tenant_id` is in their `tenant_users` set
- Authenticated internal users get a separate policy allowing cross-tenant access via service role
- Smoke test written and run to confirm tenant A cannot read tenant B's rows under any code path

### Milestone

A new user can sign up at the marketing site, log in, reach an empty `/portal` page, and the backend correctly identifies them via `/me`. Internal team members can access `/internal` after being added to the `internal_users` table.

---

## Phase 2 — Voice pipeline

**Week 2.** First successful AI call from a real phone. Single hardcoded tenant configuration. This is the highest-risk phase in v1 because it integrates four external services in real time.

### Telephony layer

- Twilio phone number purchased and configured
- Voice webhook URL pointed at backend `/webhooks/twilio/voice`
- Webhook handler returns TwiML that opens a bidirectional Media Streams websocket back to FastAPI
- Twilio status callback handler captures call completion and writes the `ended_at`, `duration_secs`, and `recording_url` fields
- mulaw 8kHz audio handling on the Twilio side, PCM 16kHz on the provider side, conversion handled inside Pipecat

### Pipecat pipeline

- Pipecat installed as a Python dependency
- Pipecat agent runs as a websocket handler inside FastAPI (not as a separate service in v1)
- Pipeline composition:
  - Twilio transport for inbound audio
  - VAD (voice activity detection) using Silero
  - STT processor (Cartesia)
  - LLM processor (DeepSeek)
  - TTS processor (Inworld)
  - Twilio transport for outbound audio
- Turn detection configured to wait for the caller to finish before generating a response
- Barge-in handling so the caller can interrupt the agent
- Agent process lifecycle managed by FastAPI: spawn on webhook, terminate on call end or timeout

### Provider implementations

The provider abstraction layer from `design.md` §4 is built in this phase. Three Python protocols (`STTProvider`, `TTSProvider`, `LLMProvider`) with one concrete implementation each:

- `CartesiaSTT` — streaming connection to Cartesia Ink-Whisper, exposes async iterator of `Transcript` objects
- `InworldTTS` — streaming TTS synthesis, returns async iterator of audio chunks
- `DeepSeekNativeLLM` — OpenAI-compatible client pointed at DeepSeek native API, supports function calling and prompt caching
- Provider registry resolves names to classes at runtime
- `make_pipeline(tenant)` factory function reads tenant `provider_config` and returns a configured Pipeline

In Phase 2 only one provider per role is wired up. Stub classes exist for the other providers (`SarvamSTT`, `TogetherDeepSeekLLM`, etc.) that raise `NotImplementedError`, establishing the abstraction shape for later phases.

### Call data capture

- `calls` row created on call start with `twilio_call_sid` and tenant/agent references
- Per-turn entries written to `call_messages` with role, content, latency, and timestamps
- Call recording downloaded from Twilio and uploaded to Supabase Storage
- `calls.recording_url` updated when storage upload completes
- `provider_snapshot` JSONB captures which providers were used (for cost forensics later)

### Performance targets

- Time to first audio (greeting playback) under 800ms
- Per-turn round-trip latency under 1.2 seconds on the 90th percentile
- Per-component latency logged so bottlenecks can be diagnosed quickly

### Milestone

Calling the Twilio number triggers a coherent back-and-forth conversation with the AI agent. Two independent testers can hold a 2-minute conversation each, and the calls land in the `calls` table with full transcripts and recording URLs.

---

## Phase 3 — Internal dashboard + multi-tenancy

**Week 3.** Tenants get configured via the internal dashboard. Phone numbers route to the correct agent per tenant. The single hardcoded path from Phase 2 generalizes.

The internal dashboard is built before the client portal because the v1 sales motion is fully team-driven — the dashboard is what the team uses to set up every new customer.

### Internal authentication

- Internal user sign-in flow at `/internal/login` validates against `internal_users` table
- Internal user session is separate from tenant user sessions
- Role-based access control: `admin` role can do everything in v1 (sales / support roles split deferred)
- Every authenticated internal-user action writes to `audit_log` with the actor's user_id and the action payload

### Tenant management APIs

- `POST /tenants` — create with business name, market, language, timezone, plan, provider_config
- `GET /tenants` — list with pagination, search by name or slug
- `GET /tenants/:id` — full detail including agents and recent calls
- `PATCH /tenants/:id` — update business info or provider_config
- `DELETE /tenants/:id` — soft delete (sets `archived_at`), hard delete only via SQL with confirmation
- All write APIs enforce RLS for tenant users and audit-log writes for internal users

### Agent management APIs

- `POST /agents` — create with name, starter prompt selection, system prompt, tools whitelist, voice_id; purchases Twilio number and wires webhook
- `GET /agents/:id` — full detail with version history
- `PATCH /agents/:id` — create new version, pin agent to new version on save
- `DELETE /agents/:id` — releases the Twilio number back to the pool

### Phone number routing

- Twilio number purchase endpoint integrates with Twilio API
- Webhook handler in `/webhooks/twilio/voice` looks up agent by `To` number
- Reads tenant `provider_config` from the agent's tenant
- Calls `make_pipeline(tenant)` to spawn the Pipecat agent with the right providers
- One Twilio account serves all tenants in v1 (sub-accounts deferred)

### Internal dashboard UI

Pages built:

- Tenant list — searchable table with pagination, filter by plan, sort by recent activity
- Tenant detail — header with business info, tabs for agents, recent calls, billing, audit log
- Tenant create form — fields for business name, vertical, timezone, phone number country, plan
- Agent create + edit form — prompt textarea with character count, tool checkboxes from the registry, voice dropdown from Inworld catalog, phone number purchase
- Audit log writes on every save

### Multi-tenant verification

Two distinct tenants are created via the dashboard with different prompts and different phone numbers. Test calls verify:

- Each number routes to its own agent
- Each agent uses its own system prompt
- Calls land in `calls` rows scoped to the correct tenant
- RLS prevents cross-tenant data access

### Milestone

Internal team can create a brand-new tenant from scratch via the dashboard in under 5 minutes, including phone number purchase. Two tenants run independently with different agents on different numbers.

---

## Phase 4 — Business brain

**Week 4.** Knowledge-base ingestion and tool calling go live. Agents become useful, not just conversational.

### Document upload

- File upload component in internal dashboard accepts PDFs
- Uploads go to Supabase Storage in a per-tenant prefix
- Storage upload returns a path that is recorded in `knowledge_documents`
- File size limits enforced (25MB per file in v1)

### Ingestion pipeline

Runs as a background job triggered by document upload:

1. PDF extraction via `pdfplumber` — page-by-page text with structure preserved
2. Text cleaning — collapse whitespace, strip headers and footers, handle bullet points
3. Chunking at 512 tokens with 64-token overlap using `tiktoken` for accurate token counts
4. Embedding via OpenAI `text-embedding-3-small` (one API call per batch of chunks)
5. Storage in `knowledge_embeddings` with `tenant_id`, `document_id`, `chunk_text`, `embedding` (vector(1536)), and metadata JSON

Background job runs in-process via APScheduler. For a 50-page PDF the full pipeline completes in 15–30 seconds.

### Vector retrieval

- pgvector extension enabled on Supabase
- `ivfflat` index on `knowledge_embeddings.embedding` with cosine distance, 100 lists
- Retrieval function: `retrieve_chunks(tenant_id, query_text, k=5, threshold=0.7)`
- Query embedding generated in-line via the same `text-embedding-3-small` model
- Top-K results filtered by cosine similarity threshold
- Per-tenant isolation guaranteed by RLS plus an explicit `WHERE tenant_id = ?` filter

### RAG integration in voice pipeline

- Before each LLM call, the user's latest utterance is embedded
- Top-5 chunks retrieved if any score above 0.7
- Retrieved chunks injected into the LLM prompt as a `context:` block before the user message
- If no chunks score above threshold, no context injected and the agent admits it doesn't know when asked specifics

### Tool registry

Tools defined as Python classes with Pydantic input schemas:

```python
class TransferToHumanInput(BaseModel):
    reason: str
    
class TransferToHumanTool:
    name = "transferToHuman"
    description = "Transfer the call to a human at the configured fallback number"
    input_schema = TransferToHumanInput
    idempotent = True
    
    async def execute(self, tenant_id: UUID, args: TransferToHumanInput) -> str:
        # ...
```

Tools available in v1:

- `transferToHuman` — transfers the call to the tenant's configured human-fallback phone number via Twilio dial verb
- `sendSms` — sends a confirmation or follow-up SMS to the caller via Twilio Messaging API
- `escalateToOwner` — sends a structured email to the business owner via Resend with call context

### Tool whitelisting and safety

- `agents.tools` is a text array of permitted tool names
- The LLM is given schemas for only the whitelisted tools (any tool call to a non-whitelisted name throws `ToolNotPermitted`)
- Input validation via Pydantic rejects malformed LLM tool calls
- Per-call rate limits prevent runaway tool calls (e.g. `sendSms` capped at 2 per call)
- Idempotency keys for stateful tools prevent duplicate execution on retry

### Post-call processing

- Background job triggered on call end
- LLM-generated summary written to `calls.summary`
- `calls.outcome` classified from the conversation (booked / transferred / info_only / abandoned)
- `calls.cost_usd` calculated from provider snapshot and duration

### Milestone

An agent given a PDF knowledge base can correctly answer KB-grounded questions during a live call and can call any of the three tools when appropriate. Post-call summaries appear in the `calls` table within 30 seconds of hang-up.

---

## Phase 5 — Client portal + billing

**Week 5.** Stripe is live. Client portal is read-only. First paying customers are onboarded by the team.

### Stripe integration

- Stripe customer created on tenant create (via webhook listener on tenant insert)
- Three subscription products created in Stripe dashboard:
  - Starter
  - Pro
  - Custom (sales-led)
- Stripe Checkout session generation endpoint
- Stripe Customer Portal link generation for plan and payment method changes
- Webhook handlers for:
  - `customer.subscription.created` — set tenant plan, activate
  - `customer.subscription.updated` — plan changes
  - `customer.subscription.deleted` — suspend tenant
  - `invoice.payment_succeeded` — confirm billing event
  - `invoice.payment_failed` — flag for follow-up

### Metered overage billing

- `billing_events` rows created per call with units (minutes) and cost_usd
- Daily aggregation job sums per-tenant overage minutes (above plan quota)
- Aggregated usage pushed to Stripe as usage records via the metered subscription item
- Stripe handles proration and invoicing at the end of the billing cycle

### Client portal

Pages built (read-only in v1):

- Dashboard — header with current plan and usage, call volume chart for last 7 days, recent calls list
- Calls list — paginated table with date filter, outcome filter, agent filter
- Call detail — header with call metadata, full per-turn transcript, embedded audio player for the recording
- Billing — current plan card, current usage card, next invoice estimate, "Manage Billing" button that opens Stripe Customer Portal

### Compliance endpoints

- `GET /tenants/me/export` — returns a JSON dump of all tenant data (DPDP / GDPR-style data export)
- `DELETE /tenants/me` — hard delete with cascade after confirmation flow (requires re-authentication)
- Pre-call consent disclosure played as TwiML before agent connects ("This call may be recorded for quality and AI assistance")
- Recording retention job: deletes recordings older than 30 days

### Observability

- Sentry SDK initialized on Next.js with `beforeSend` hook to scrub phone numbers, emails, and names from breadcrumbs
- Sentry SDK initialized on FastAPI with the same scrubbing rules
- Custom error categories registered: `voice_pipeline_error`, `llm_error`, `tool_error`, `integration_error`, `billing_error`
- Frontend error boundaries that report to Sentry and show a graceful fallback

### Customer onboarding

- Team uses the internal dashboard to onboard the first cohort:
  - Tenant created with business info collected via a 15-minute discovery call
  - System prompt customized from the generic starter
  - PDF FAQs uploaded via the dashboard
  - Phone number purchased and given to the customer
  - Customer pointed to the client portal for call logs

### Milestone

First paying customers on active Stripe subscriptions, each taking real calls within 48 hours of activation.

---

## Week 6 — Buffer and customers

Reserved for stabilization, additional customer onboarding, and v1.5 preparation.

### Stabilization

- Triage bugs reported by the first customers and prioritize fixes
- Listen to 3 random call recordings per customer per day, log quality issues
- Review every Sentry error from the past week, categorize as real bug, noise, or ignorable
- Add focused tests for the bugs that came up

### Additional customers

- Continue onboarding customers via the internal dashboard
- Refine the discovery call script based on what the first few customers needed
- Refine the starter prompt based on what worked vs. what got edited heavily

### Marketing assets

- 60-second demo video on the landing page showing an AI agent take a call
- One-page "how it works" doc linked from marketing
- Pricing page updated with real plan details and a customer logo strip

### v1.5 sprint planning

- 15-minute interview with each v1 customer: what works, what doesn't, what would they pay more for
- Retro: what the team learned in 5 weeks, what to change for v1.5
- Sprint plan for v1.5 (4 weeks, weeks 7–10) drafted based on customer feedback

---

## Ordering rationale

Why phases are ordered this way:

**Foundation first (Phase 1)** because every other phase depends on schemas, RLS, and authenticated routing. Building schemas later forces migrations on production data.

**Voice pipeline second (Phase 2)** because it's the highest technical risk and the highest learning load. If something is going to slip, it's better to find out in week 2 than in week 4.

**Internal dashboard third (Phase 3)** before the brain because the brain needs to be configurable per tenant — the dashboard is what enables tenant-specific configuration. Building the dashboard first also matches the sales motion: every v1 customer is configured through the dashboard.

**Business brain fourth (Phase 4)** because RAG and tools turn the agent from a chatbot into a useful product. Adding them after the dashboard means each tenant created in Phase 3 can immediately get a knowledge base and tools configured.

**Client portal and billing fifth (Phase 5)** because customers don't need the portal to be live until they're paying — and they're not paying until billing works. Both ship together at the end so that the first paid customers see a complete experience.

---

*End of mvp-planning.md*
