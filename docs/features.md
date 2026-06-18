# Features

Feature inventory organized by version, then by area within each version. Each feature includes a brief description of what it does.

See `roadmap.md` for timing and strategic context, `mvp-planning.md` for v1 execution, and `design.md` for architecture.

---

## v1 — MVP

### Telephony

- **Inbound calls via Twilio Voice** — handles real-time bidirectional audio through Twilio Media Streams websockets
- **Phone number provisioning** — programmatic purchase of Indian local numbers via the Twilio API, one per agent
- **One agent per phone number per tenant** — webhook resolution by `To` number, no number sharing between tenants
- **Call recording** — Twilio records both legs, recording URL stored in Supabase Storage and referenced in the `calls` row
- **Pre-call consent disclosure** — TwiML plays a recorded notice ("This call may be recorded for quality and AI assistance") before connecting to the agent

### Voice orchestration

- **Pipecat self-hosted** — Pipecat framework runs inside the FastAPI process, not as a separate managed service
- **Provider abstraction layer** — Python protocols (`STTProvider`, `TTSProvider`, `LLMProvider`) with a registry and factory for runtime resolution
- **DeepgramSTT** — streaming Nova-3 Monolingual integration as the first concrete STT provider
- **DeepgramTTS** — Aura-1 streaming synthesis as the first concrete TTS provider
- **DeepSeekNativeLLM** — DeepSeek V4 Flash via the OpenAI-compatible native API
- **Prompt caching** — system prompts stored verbatim so DeepSeek's 50× cache discount applies
- **VAD (voice activity detection)** — Silero VAD via Pipecat default
- **Turn detection** — waits for caller to finish before generating response
- **Barge-in** — caller can interrupt agent mid-response
- **Hardcoded default voice per agent** — single Deepgram Aura voice across v1, swap requires admin edit
- **Per-turn latency logging** — every turn writes a `latency_ms` to `call_messages` for performance forensics

### Business brain — system prompt

- **Per-agent stored system prompt** — final assembled prompt saved verbatim to `agents.system_prompt`
- **Generic configurable starter prompt** — single base template that adapts to any vertical via tenant variables
- **Prompt assembly from template** — assembled once at agent-create time, not per call (preserves cache hit)
- **Custom rules editor** — free text field appended to the assembled prompt for tenant-specific dos and don'ts
- **Prompt versioning** — every save creates a new `version` row; agents pinned to a specific version
- **Version pinning** — agent does not pick up prompt changes unless explicitly upgraded
- **Concise-response budget** — prompt enforces ≤25-word replies, which caps per-minute TTS cost since Aura is character-billed

### Business brain — knowledge base

- **PDF upload and ingestion** — pdfplumber extracts text, background job processes asynchronously
- **Chunking** — 512-token chunks with 64-token overlap, tokenized with tiktoken for accuracy
- **OpenAI text-embedding-3-small** — cheapest reasonable embedding model, $0.02 per 1M tokens
- **pgvector storage** — embeddings stored in `knowledge_embeddings` table with ivfflat index, 100 lists
- **Top-K retrieval** — top 5 chunks by cosine similarity, threshold 0.7 to filter weak matches
- **Per-tenant retrieval isolation** — both RLS and explicit `WHERE tenant_id` clause
- **Context injection** — retrieved chunks injected as `context:` block before the user message in LLM calls
- **Document re-ingestion** — re-embeds when content changes, replacing previous chunks
- **Knowledge browser in internal dashboard** — list, view, delete documents per tenant

### Business brain — tools

- **Tool registry** — Python module registers tools with name, description, schema, and execute function
- **Per-agent tool whitelist** — `agents.tools` text array filters which tools the LLM sees
- **transferToHuman** — transfers the call to the tenant's configured human-fallback number via Twilio dial verb
- **sendSms** — sends a confirmation or follow-up SMS to the caller via Twilio Messaging API
- **escalateToOwner** — sends a structured email to the business owner via Resend with call context and transcript snippet
- **Pydantic schema validation** — rejects malformed LLM tool calls before execution
- **Per-call rate limiting** — prevents runaway tool calls (e.g. sendSms capped at 2 per call)

### Workflow engine

- **Default Pipecat conversation loop** — no custom state machine in v1, Pipecat handles turn-taking
- **Auto-summary at call end** — LLM-generated one-paragraph summary written to `calls.summary` by background job
- **Escalation triggers** — three consecutive low-confidence intents auto-trigger `transferToHuman` or `escalateToOwner`

### Internal dashboard

- **Internal user authentication** — separate auth path at `/internal/login`, validates against `internal_users` table
- **Admin role** — single role in v1 with full access to all tenants
- **Tenant list view** — searchable, paginated, sortable table of all tenants
- **Tenant detail view** — header with business info, tabs for agents, calls, billing, audit log
- **Tenant create form** — business name, vertical, timezone, country, plan selection
- **Agent create and edit** — prompt textarea, tool whitelist checkboxes, voice dropdown from the Deepgram Aura catalog, phone number purchase
- **Knowledge upload for any tenant** — internal team uploads on behalf of customers in v1
- **Call viewer with transcript and playback** — per-turn transcript display with embedded audio player
- **Audit log writes** — every internal-user action writes a row with actor, action, and payload

### Client portal

- **Tenant user authentication** — Supabase Auth with email and password
- **Dashboard with call volume chart** — bar chart of last 7 days, today's total, recent calls preview
- **Call logs list** — paginated table with date filter and outcome filter
- **Call detail view** — full per-turn transcript and embedded audio player
- **Billing page (read-only)** — current plan card, usage card, and access window ("valid until" date)
- **Renew via contact** — "Contact us to renew" (lead form / email); no self-serve payment in v1

### Landing and marketing

- **Marketing landing page** — hero, features section, social proof, CTAs that open the lead-capture dialog (book a demo / contact sales) — paid-only, no free trial, no self-serve signup in v1
- **Pricing page** — three plan tiers with comparison table (informational; payment is arranged with the team)
- **Live demo call number** — published Twilio number that calls a demo tenant agent so prospects can try
- **Lead capture form** — drops captured leads into Resend email to the sales team

### Onboarding

- **Sales-led configuration** — entire onboarding handled by the internal team through the dashboard in v1
- **Lead capture to sales notification** — form submissions trigger an email and a Sentry breadcrumb

### Billing & onboarding payments (v1: manual, no gateway)

- **Sales-led onboarding** — after a lead and an email conversation, the team provisions the tenant and issues a login valid for the paid period
- **Manual / offline payment** — UPI / bank transfer agreed over email and recorded by the team; no payment gateway in v1
- **Time-bound access (`paid_until`)** — agents answer only while the paid period is active; an expiry job pauses lapsed tenants until renewal
- **Recorded payments** — the team logs each payment (amount, method, period, reference), which extends `paid_until` and writes a `billing_events` row
- **Usage rollup** — daily aggregation of minutes + cost into `billing_events` for the portal usage card and manual invoicing
- **Pricing plans (config)** — Starter, Pro, and Custom defined in `pricing_plans` for the pricing page + invoicing reference
- **Payment gateway** — deferred; a real gateway (Razorpay / Cashfree, India-friendly) is planned for a later phase

### Observability

- **Sentry frontend integration** — Next.js plugin captures unhandled errors, performance, and user feedback
- **Sentry backend integration** — FastAPI plugin captures exceptions and slow transactions
- **PII scrubbing** — `beforeSend` hook strips phone numbers, emails, names, and call audio paths from breadcrumbs
- **Custom error categories** — voice_pipeline_error, llm_error, tool_error, integration_error, billing_error
- **Structured logging** — structlog with JSON output for production log analysis
- **Per-turn latency tracking** — `call_messages.latency_ms` enables p50, p95, p99 analysis per provider
- **TTS chars-per-turn tracking** — recorded per turn as a cost-control signal since Aura is character-billed

### Compliance and security

- **TLS in transit** — required on every external connection
- **Encryption at rest** — Supabase default (AES-256)
- **Multi-tenant RLS policies** — Postgres Row Level Security on every tenant-scoped table
- **Tenant data export** — JSON dump endpoint for DPDP / GDPR-style data export requests
- **Tenant data deletion** — hard cascade delete with re-authentication confirmation
- **Audit log** — every internal-user action recorded for compliance and debugging
- **API keys as platform secrets** — never committed to git, stored in Render/Vercel secret managers
- **Call recording retention** — 30-day default, automatic deletion job for older recordings
- **DPDP Act basics** — data residency in `ap-south-1` (Supabase, Upstash) and Singapore (Render)

### Language

- **English (Indian accent)** — default language in v1, supported across Deepgram Nova-3 / Aura and DeepSeek

---

## v1.5 — Self-serve + booking

### Telephony

- **Inbound SMS handling** — process SMS messages to agent numbers as a separate workflow path

### Voice orchestration

- **Voice selection per agent UI** — dropdown in client portal showing the Deepgram Aura voice catalog with previews
- **Aura-2 upgrade option** — clients can opt into the higher-quality Aura-2 voice at a different per-character rate
- **Krisp noise cancellation** — Pipecat plugin reduces background noise in clinic and restaurant environments

### Business brain — system prompt

- **Four additional starter prompts** — receptionist, restaurant, hotel, and retail templates pre-built
- **Prompt rollback** — one-click revert to any previous version
- **Tone modifiers** — formal, casual, warm options inserted into the starter template

### Business brain — knowledge base

- **Manual FAQ entry form** — direct question + answer pairs entered in the client portal
- **URL scrape and ingestion** — fetch a URL, clean with trafilatura, chunk and embed the same way as PDFs
- **Knowledge browser in client portal** — clients manage their own knowledge documents
- **Google Sheets sync** — periodic pull from a published CSV URL keeps a KB section auto-updated

### Business brain — tools

- **checkAvailability** — checks available slots in the tenant's calendar for a requested time range
- **bookAppointment** — creates a booking in the tenant's calendar with caller name and contact
- **cancelAppointment** — looks up and cancels an existing booking
- **rescheduleAppointment** — combines cancel and book for date changes
- **Google Calendar OAuth and integration** — per-tenant OAuth flow during onboarding, calendar API for read and write
- **lookupOrder** — webhook-based tool that calls the tenant's configured CRM/POS endpoint to look up an order
- **Tool idempotency keys** — prevents duplicate execution of stateful tools on retry

### Workflow engine

- **Custom state machine via Pipecat Flows** — explicit states for greet, intent, action, confirm, end
- **Per-state tool availability** — tools only callable in appropriate states (e.g. `bookAppointment` only in action state)
- **Workflow analytics per state** — funnel showing where callers drop off in the conversation

### Internal dashboard

- **Audit log viewer** — searchable UI for the audit_log table with filters by actor, action, and tenant
- **Global metrics dashboard** — today's call volume, active tenants, top errors across all tenants
- **Prompt template management** — CRUD on the starter templates accessible from the dashboard
- **Tenant suspension and unsuspension** — cuts off webhook routing without deleting data
- **Refund issuance** — via the payment gateway once integrated (manual refund in v1), with audit log entry

### Client portal

- **OAuth (Google sign-in)** — Supabase Auth supports out of the box
- **Knowledge management UI** — upload, list, delete documents from the client portal
- **System prompt editor** — edit the assembled prompt directly with character count and version history
- **Voice selection dropdown** — change Deepgram Aura voice with audio preview
- **Tool whitelist editor** — toggle which tools the agent has access to
- **Phone number management** — buy additional numbers, release unused ones
- **FAQ editor** — lightweight knowledge-base path for tenants who don't have PDFs
- **Invoice download as PDF** — manual invoice in v1; gateway-generated once a payment gateway is integrated
- **Test call simulator** — "Call my phone" button triggers a Twilio call from the configured agent to the user's number

### Landing and marketing

- **60-second demo video** — embedded on landing page showing an AI agent take a call
- **Embed-able text demo widget** — try-before-call demo on the landing page using the same DeepSeek prompt
- **Case studies** — static pages with customer stories
- **Testimonials section** — quotes from v1 customers
- **Help center / docs site** — Mintlify or Docusaurus-based public documentation

### Onboarding

- **Self-serve 5-step wizard** — business info, knowledge upload, starter prompt, tools, phone number
- **Starter prompt picker UI** — five cards with previews, one-click selection
- **Knowledge upload during wizard** — PDF or URL or manual FAQ within the flow
- **Phone number purchase during wizard** — inline Twilio API call, customer sees their number provisioned
- **Test call during wizard** — last step calls the customer's phone to verify the agent works
- **Funnel analytics per step** — PostHog tracks completion rate at every wizard step
- **Auto-suggest starter based on vertical** — pre-selects the right template from the business-info input

### Billing

- **Payment gateway integration** — Razorpay / Cashfree (India-friendly) for self-serve subscriptions, replacing v1 manual payment
- **Failed payment retry and dunning** — handled by the payment gateway once integrated
- **Refunds (internal-team initiated)** — via the payment gateway once integrated, with audit log entry
- **Annual billing discount** — coupon / discount applied via the gateway or the manual invoice

> **No free trial** — the product is paid-only. There is no trial tier; access begins after payment and is bounded by `paid_until`.

### Observability

- **PostHog product analytics** — funnel tracking, event capture, session replay for the onboarding flow
- **Per-tenant metrics dashboard** — call volume, resolution rate, transfer rate, cost per call in client portal
- **Per-call quality auto-flags** — sentiment drop, multiple "I'm not sure" replies, tool failures
- **Manual review queue** — flagged calls appear in an internal dashboard queue for human review
- **Eval pipeline** — daily background job samples 5% of calls, replays through current prompt, flags regressions
- **Sentiment analysis per turn** — LLM-tagged sentiment on each agent message for trend analysis

---

## v2 — India Hindi + depth

### Telephony

- **Multiple phone numbers per agent** — one agent can serve multiple locations or campaigns

### Voice orchestration

- **SarvamSTT provider** — concrete implementation for Sarvam streaming STT, supports Indian languages including native Hinglish code-switching
- **SarvamTTS provider** — concrete implementation for Sarvam TTS with multiple Indian voices
- **Deepgram Nova-3 Multilingual option** — alternative for tenants whose customers code-switch between English and Hindi but lean English-dominant

### Business brain — system prompt

- **Hindi starter prompts** — translations of the five English starters into Hindi

### Business brain — knowledge base

- **Audio transcript ingestion** — upload existing call recordings and ingest the transcripts as KB content

### Business brain — tools

- **Calendly integration** — API-driven booking through Calendly's REST API
- **Microsoft Outlook calendar** — adds Outlook to the calendar provider abstraction
- **Custom webhook tool** — client defines a webhook URL and JSON schema, agent calls it as a generic tool
- **Slack notification on escalation** — Slack incoming webhook for tenant-specific channels
- **WhatsApp Business reply** — outbound WhatsApp message after call via WhatsApp Business API

### Workflow engine

- **Conversation memory across long calls** — summarizes earlier turns when context window grows large

### Internal dashboard

- **Real-time call monitoring** — live transcript stream of ongoing calls visible to internal team
- **Tool catalog management** — add and configure tools through the dashboard without code deploys
- **Eval pipeline results viewer** — UI for browsing daily replay regression results

### Client portal

- **Team member invites** — multiple users per tenant with email-invite flow

### Landing and marketing

- **Blog** — MDX-based, SEO-optimized content marketing
- **Comparison pages** — "vs Vapi", "vs Retell", "vs Synthflow" for buyer research
- **Multilingual landing page** — Hindi version of the marketing site

### Onboarding

- **Pre-fill business info from URL** — scrapes the customer's existing website to populate business info
- **Resume incomplete onboarding** — email reminder with saved state if a customer abandons mid-wizard
- **Concierge onboarding bot** — AI agent walks new customers through the wizard via chat
- **Onboarding video tutorials** — Loom-style videos for each wizard step

### Billing

- **INR + USD multi-currency** — handled by the payment gateway once integrated; portal UI shows the right currency

### Observability

- **Real-time alerting** — PagerDuty or email alerts on critical error patterns
- **Provider latency comparison** — which STT/TTS/LLM provider is fastest right now across all tenants
- **Cost anomaly detection** — alert when a tenant's daily cost spikes 3× over their trailing average

### Compliance and security

- **GDPR compliance** — right to be forgotten, broader data handling commitments

### Languages

- **Hindi (Devanagari and Hinglish)** — full support for Hindi with code-switching
- **Code-switching mid-sentence** — handled natively by Sarvam STT
- **Per-tenant language configuration** — `tenants.language` drives provider selection at agent spawn
- **Bengali (stretch)** — Sarvam supports, validated against market demand first
- **Tamil (stretch)** — same
- **Marathi (stretch)** — same

---

## v3 — US HIPAA + enterprise

### Telephony

- **Twilio HIPAA-eligible variant** — BAA add-on, separate webhook handling
- **Number porting (BYO)** — paid service tier, multi-week carrier paperwork process

### Voice orchestration

- **DeepgramSTTEnterprise (BAA)** — Nova-3 Monolingual on the Enterprise tier with a signed BAA, same code path as the standard provider with a new registry name
- **DeepgramTTSEnterprise (BAA)** — Aura-1 on the Enterprise tier with a signed BAA — same single-vendor BAA covers both voice layers
- **Together AI DeepSeek (BAA)** — new `TogetherDeepSeekLLM` implementation, US-hosted, HIPAA-eligible
- **OpenAI Realtime fallback** — bundled STT+LLM+TTS option for global English markets

### Business brain — system prompt

- **A/B testing two prompt versions** — 50/50 split on incoming calls, compare resolution rates

### Business brain — knowledge base

- **Re-ranking with second model** — improves precision for ambiguous queries
- **Knowledge base versioning** — track changes over time, browse history
- **Auto-ingest from website crawl** — sitemap-driven, periodic re-crawl

### Business brain — tools

- **Salesforce integration** — direct API integration for the enterprise CRM
- **HubSpot integration** — same for HubSpot
- **Toast / Petpooja POS integration** — restaurant-specific point-of-sale connectors
- **Practo / clinic management software** — clinic-specific patient management connectors

### Workflow engine

- **Custom workflow per tenant** — tenant defines their own state machine via dashboard or API

### Internal dashboard

- **Cost forecasting per tenant** — projected monthly bill from current usage trend
- **Multi-team support** — India team vs US team scoped views and permissions

### Client portal

- **Custom domain for portal** — `clinic.example.com` redirects to the client portal
- **White-label option** — remove platform branding for resellers
- **Webhook events to client** — `call.ended`, `call.transferred`, etc. delivered to client-defined endpoints
- **Public API for clients** — programmatic access to tenant data

### Onboarding

- **Bulk import** — CSV upload for sales-led batch tenant creation
- **In-app product tour** — first-time UI walkthrough for new tenant users

### Billing

- **Per-line pricing** — charge per active phone number rather than per-tenant flat rate
- **Enterprise custom contracts** — manual contract terms with manual / gateway invoicing

### Observability

- **Distributed tracing** — OpenTelemetry traces calls across services for deep performance analysis

### Compliance and security

- **HIPAA-eligible provider configuration** — provider abstraction selects BAA-eligible providers per tenant
- **SOC 2 Type II audit** — external auditor, 3–6 month parallel work
- **HIPAA BAA execution** — signed BAAs with Together AI, Twilio, Deepgram Enterprise (single BAA covering both STT and TTS)
- **Penetration testing** — one-time engagement before US launch
- **Granular role-based permissions** — beyond admin/member, fine-grained roles like "billing only", "read only"

### Languages

- **English (US accent)** — same provider stack as Indian English with US-targeted Aura voices
- **Spanish** — OpenAI TTS or ElevenLabs for synthesis where Aura coverage is limited
- **French** — same

---

## Future

Only built when a paying customer explicitly demands and commits.

### Telephony

- **Outbound dialing** — sales and notification campaigns, different compliance scope (DNC, TRAI)
- **IVR phone tree integration** — "Press 1 for English" flows before AI agent picks up
- **Call queueing with hold music** — when concurrent slots are saturated
- **International number support** — beyond India and US (UK, AU, etc.)

### Voice orchestration

- **Custom voice cloning per client** — Deepgram Aura ships with a curated voice catalog; custom voices are an Enterprise conversation
- **Mid-call language switching** — caller starts in English, switches to Hindi mid-conversation

### Business brain — system prompt

- **Per-time-of-day prompt variants** — different greetings during business hours vs after-hours
- **Prompt linter** — static analysis catching common prompt-writing mistakes

### Business brain — knowledge base

- **LLM-generated KB from transcripts** — mine production call transcripts to auto-create FAQs

### Business brain — tools

- **Voice payments (Razorpay)** — collect payment info via voice, PCI scope expansion
- **Tool marketplace** — third-party developers publish tools for tenants to install

### Workflow engine

- **Visual workflow editor** — drag-and-drop state machine builder
- **Conditional branches** — "if new customer, go to onboarding state"

### Internal dashboard

- **Bulk operations** — for 100+ tenants, batch actions like export, message, suspend

### Client portal

- **Mobile app** — native iOS and Android apps

### Landing and marketing

- **Partner / reseller program** — formal channel partnerships with chamber commerce, agencies

### Billing

- **Reseller marketplace billing** — partners bill end clients, we bill partners

### Observability

- **Voice quality measurements (MOS)** — audio quality metrics per call

### Compliance and security

- **PCI DSS** — only if voice payments ship
- **Bug bounty program** — at meaningful scale via HackerOne or similar

### Languages

- **Arabic** — requires RTL UI work in addition to TTS/STT
- **Others on demand** — driven by customer requests

---

_End of features.md_
