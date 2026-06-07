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

| Endpoint                       | Auth                 | Description                        |
| ------------------------------ | -------------------- | ---------------------------------- |
| `GET /`                        | No                   | Hello-world                        |
| `GET /health`                  | No                   | Status + timestamp + DB            |
| `GET /me`                      | Bearer JWT           | User + tenant + role               |
| `GET /internal/ping`           | Internal JWT         | Cross-tenant ping + audit          |
| `POST /webhooks/twilio/voice`  | Twilio signature     | Inbound call → TwiML Media Stream  |
| `POST /webhooks/twilio/status` | Twilio signature     | Call status callbacks (204)        |
| `WS /webhooks/twilio/media`    | Twilio Media Streams | Pipecat voice pipeline (2.04–2.05) |
| `GET /internal/tenants`        | Internal JWT         | Paginated tenant list              |
| `GET /internal/tenants/{id}`   | Internal JWT         | Tenant detail + agents/calls/audit |
| `POST /internal/tenants`       | Internal JWT         | Create tenant                      |
| `PATCH /internal/tenants/{id}` | Internal JWT         | Update tenant                      |
| `GET /docs`                    | No                   | OpenAPI                            |

## Twilio webhooks (ticket 2.02)

Set `TWILIO_AUTH_TOKEN` (from 2.01) and `PUBLIC_API_BASE_URL` to the URL Twilio POSTs to
(e.g. `https://ai-voice-ocy9.onrender.com` or your ngrok URL in 2.03).

Point the Twilio number **Voice webhook** at `POST {PUBLIC_API_BASE_URL}/webhooks/twilio/voice`
and **Status callback** at `POST {PUBLIC_API_BASE_URL}/webhooks/twilio/status`.

For local TwiML testing without credentials, set `TWILIO_SIGNATURE_VALIDATION=false` (dev only).

Invalid or missing signatures return `403` with `{"detail":{"code":"...","message":"..."}}`.

## Twilio Media Streams (tickets 2.04–2.05)

The voice webhook TwiML opens `WS {PUBLIC_API_BASE_URL}/webhooks/twilio/media`. On connect:

- **With `DEEPGRAM_API_KEY`**: Pipecat converts Twilio μ-law 8 kHz ↔ linear16 PCM (16 kHz STT
  ingress, 8 kHz TTS egress), runs Deepgram STT + TTS, and speaks a short greeting.
- **Without Deepgram**: plays a static hello tone (2.04 fallback).

Set `DEEPGRAM_API_KEY` from [console.deepgram.com](https://console.deepgram.com). Optional
`DEEPGRAM_VOICE` defaults to `aura-2-helena-en`.

Pipeline code: `app/services/voice/pipeline.py`, rates in `audio_config.py`. Lifecycle logs:
`twilio_pipeline_*`, `deepgram_stt_*`, `audio_buffer_underrun`, `twilio_media_websocket_*`.

Optional: set `TWILIO_ACCOUNT_SID` with `TWILIO_AUTH_TOKEN` so Pipecat can auto-hang-up when
the stream ends.

## Auth

```http
Authorization: Bearer <supabase_access_token>
```

Errors: `{"detail": {"code": "...", "message": "..."}}`

## Clients

| Client                                         | Use for                                          |
| ---------------------------------------------- | ------------------------------------------------ |
| **asyncpg** (`DATABASE_URL`)                   | User-scoped DB access                            |
| **Service role** (`get_service_role_client()`) | PostgREST via httpx — internal / RLS bypass only |

## Tests

```bash
pnpm --filter @ai-voice/api run test
```

## Production (Render)

Deploy via the root [`render.yaml`](../../render.yaml) Blueprint (Singapore region, auto-deploy from `main`).

Full setup, env vars, and cron-job.org warm-ping: **[docs/deploy-render.md](../../docs/deploy-render.md)**.

```bash
# Local production-style run (port 8000)
pnpm --filter @ai-voice/api run start
```
