# AI Voice

[![CI](https://github.com/Shubhamraj8/ai-voice/actions/workflows/ci.yml/badge.svg)](https://github.com/Shubhamraj8/ai-voice/actions/workflows/ci.yml)

AI Voice is a multi-tenant AI voice agent platform for small businesses. The product is designed to let businesses handle inbound phone calls with configurable AI agents while keeping the backend flexible enough to swap telephony, speech, and language providers by tenant.

## Status

**Phase 1 (foundation) and Phase 2 (voice pipeline) are complete.**

- **Phase 1 — foundation:** monorepo + tooling, Supabase multi-tenant schema with
  row-level security, Supabase auth with route guards, marketing site, client
  portal and internal dashboard shells, and Render/Vercel deployment.
- **Phase 2 — voice pipeline:** end-to-end inbound calls over Twilio Media
  Streams — Deepgram STT (Nova-3) → DeepSeek LLM → Deepgram TTS (Aura) with
  VAD-based turn detection and barge-in. Includes call and per-turn persistence,
  call recording to Supabase Storage, per-turn latency metrics, a sub-800ms
  greeting and a consent disclosure on pickup, and agent-process lifecycle
  management. End-to-end real-call testing (ticket 2.19) is the final validation
  step before Phase 3.

## Monorepo structure

```text
/apps
  /web                # Next.js 14 frontend
  /api                # FastAPI backend
/packages
  /db                 # Postgres migrations and shared types
  /shared             # Shared TypeScript types and Zod schemas
/docs                 # product and architecture docs
```

## Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.11+

## Setup

From the repository root:

```bash
pnpm install
pnpm --filter @ai-voice/api run install:python
cp .env.example .env
# Add Supabase credentials, then:
pnpm --filter @ai-voice/db run migrate:up
```

See `packages/db/README.md` for Supabase project setup steps.

Or use the combined setup script:

```bash
pnpm setup
```

## Development

Run both apps in parallel:

```bash
pnpm dev
```

- Web: http://localhost:3000 — marketing site, client portal, and internal dashboard
- API: http://localhost:8000 — Twilio voice webhooks and internal endpoints

## Dev tunnel (Twilio webhooks)

Twilio webhooks require a publicly reachable URL. During local development, use
ngrok to expose the local FastAPI server.

### 1. Install ngrok

```powershell
# Windows (any one of):
winget install ngrok.ngrok
choco install ngrok
scoop install ngrok
```

Or download from <https://ngrok.com/download> and add to `PATH`.

### 2. Add your ngrok authtoken

Sign up at <https://dashboard.ngrok.com>, copy your authtoken, and add it to `.env`:

```env
NGROK_AUTHTOKEN=your_ngrok_authtoken
```

> **Stable subdomain (paid plan):** Set `NGROK_SUBDOMAIN=your-name` to get a fixed URL so
> you only need to configure the Twilio webhook once.

### 3. Start everything with one command

```powershell
.\scripts\dev-with-tunnel.ps1
```

This script:

- Loads `.env` into the current shell
- Starts ngrok → `localhost:8000`
- Prints the public webhook URL to paste into Twilio Console
- Starts FastAPI + Next.js (`pnpm dev`) in the foreground
- Kills ngrok automatically when you press Ctrl+C

Alternatively, start just the tunnel (ngrok only, no dev server):

```bash
python apps/api/scripts/dev_tunnel.py
```

### 4. Configure Twilio

Paste the printed URL into the Twilio Console:

```
Phone Numbers → Manage → Active Numbers → <your number> → Voice Configuration
Voice URL: https://<your-id>.ngrok-free.app/webhooks/twilio/voice   [HTTP POST]
```

> **Auto-update:** Set `TWILIO_AUTO_UPDATE_WEBHOOK=true` in `.env` and the tunnel
> script will update the Twilio Voice URL automatically on each start.

### Switching between dev and production

| Environment | `PUBLIC_API_BASE_URL`                |
| ----------- | ------------------------------------ |
| Local dev   | `https://<id>.ngrok-free.app`        |
| Production  | `https://ai-voice-ocy9.onrender.com` |

Update `PUBLIC_API_BASE_URL` in `.env` (local) or in the Render Dashboard (production)
whenever the URL changes. The ngrok free tier assigns a new URL on every restart —
a paid subdomain or `TWILIO_AUTO_UPDATE_WEBHOOK=true` avoids this.

## Quality checks

From the repository root:

```bash
pnpm lint
pnpm typecheck
pnpm format:check
```

Or run everything together:

```bash
pnpm validate
```

After migration `006` and `.env` are configured, run the cross-tenant RLS smoke test:

```bash
python -m pip install -r packages/db/requirements-test.txt
pnpm test:rls
```

A Husky pre-commit hook runs `lint-staged` and `typecheck` before each commit.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Documentation

- `docs/design.md` - system architecture and technical design
- `docs/features.md` - feature inventory by version
- `docs/mvp-planning.md` - week-by-week MVP execution plan
- `docs/roadmap.md` - longer-term product roadmap
- `docs/tickets.md` - implementation tickets
