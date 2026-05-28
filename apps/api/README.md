# AI Voice API

FastAPI backend (ticket 1.10+).

## Setup

From repo root:

```bash
cp .env.example .env
# Set DATABASE_URL and optional CORS_ORIGINS

pnpm --filter @ai-voice/api run install:python
```

## Run

```bash
pnpm --filter @ai-voice/api dev
```

- http://127.0.0.1:8000/ — hello-world
- http://127.0.0.1:8000/health — DB pool ping (JSON logs on stdout)

## Environment

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase Postgres direct URI (required) |
| `CORS_ORIGINS` | Comma-separated origins (default `http://localhost:3000`) |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` (default `INFO`) |

Logs are structured JSON via structlog. Each request gets an `X-Request-ID` header.
