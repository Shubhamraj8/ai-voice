# AI Voice

AI Voice is a planned multi-tenant AI voice agent platform for small businesses. The product is designed to let businesses handle inbound phone calls with configurable AI agents while keeping the backend flexible enough to swap telephony, speech, and language providers by tenant.

## Status

This repository is currently in the planning and architecture phase. The app is not implemented yet.

The current repository includes:

- product and architecture design
- MVP execution planning
- feature inventory
- roadmap planning

## Project vision

The long-term goal is to build a multi-vertical, multi-market voice AI platform where the same core system can support businesses such as clinics, restaurants, hotels, and retail stores through configuration rather than separate codebases.

The planned MVP focuses on:

- India English as the first market
- inbound Twilio-based voice handling
- provider abstraction for STT, TTS, and LLM services
- multi-tenant architecture with strong tenant isolation
- an internal dashboard for team-led onboarding

## Planned stack

- Frontend: Next.js
- Backend: FastAPI
- Database and auth: Supabase / Postgres
- Telephony: Twilio
- Voice pipeline: Pipecat
- Observability and supporting services: Sentry, Resend, Stripe, Upstash

## Repository docs

- `docs/design.md` - system architecture and technical design
- `docs/features.md` - feature inventory by version
- `docs/mvp-planning.md` - week-by-week MVP execution plan
- `docs/roadmap.md` - longer-term product roadmap

## Planned repository structure

```text
/apps
  /web
  /api
/packages
  /db
  /shared
/docs
```

## First milestone

The first milestone is to ship an MVP that can run real inbound AI voice calls for initial customers, with the core architecture in place for later market and provider expansion.
