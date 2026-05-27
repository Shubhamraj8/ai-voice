# AI Voice

[![CI](https://github.com/Shubhamraj8/ai-voice/actions/workflows/ci.yml/badge.svg)](https://github.com/Shubhamraj8/ai-voice/actions/workflows/ci.yml)

AI Voice is a multi-tenant AI voice agent platform for small businesses. The product is designed to let businesses handle inbound phone calls with configurable AI agents while keeping the backend flexible enough to swap telephony, speech, and language providers by tenant.

## Status

Phase 1 implementation is in progress. The monorepo includes a Next.js frontend and a FastAPI backend.

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

- Web: http://localhost:3000
- API: http://localhost:8000

Both apps expose `hello-world` on their root paths.

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

A Husky pre-commit hook runs `lint-staged` and `typecheck` before each commit.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Documentation

- `docs/design.md` - system architecture and technical design
- `docs/features.md` - feature inventory by version
- `docs/mvp-planning.md` - week-by-week MVP execution plan
- `docs/roadmap.md` - longer-term product roadmap
- `docs/tickets.md` - implementation tickets
