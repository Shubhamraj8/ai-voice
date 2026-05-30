# AI Voice API

FastAPI backend (tickets 1.10–1.13).

## Setup

```bash
cp .env.example .env
# DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY required

pnpm --filter @ai-voice/api run install:python
```

## Run

```bash
pnpm --filter @ai-voice/api dev
```

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /` | No | Hello-world |
| `GET /health` | No | Status + timestamp + DB |
| `GET /me` | Bearer JWT | User + tenant + role |
| `GET /internal/ping` | Internal JWT | Cross-tenant ping + audit |
| `GET /docs` | No | OpenAPI |

## Auth

```http
Authorization: Bearer <supabase_access_token>
```

Errors: `{"detail": {"code": "...", "message": "..."}}`

## Clients

| Client | Use for |
|--------|---------|
| **asyncpg** (`DATABASE_URL`) | User-scoped DB access |
| **Service role** (`get_service_role_client()`) | PostgREST via httpx — internal / RLS bypass only |

## Tests

```bash
pnpm --filter @ai-voice/api run test
```
