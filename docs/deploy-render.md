# Render deployment + warm-ping (ticket 1.17)

Deploy the FastAPI backend to [Render](https://render.com) on the **Singapore** region and keep the free-tier web service warm with an external cron.

## Prerequisites

- GitHub repo connected to Render
- Supabase project with `DATABASE_URL`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`
- Migrations applied (`pnpm migrate:up`)

## 1. Create the web service (Blueprint)

1. Render Dashboard → **New** → **Blueprint**
2. Connect `Shubhamraj8/ai-voice` (or your fork)
3. Render reads [`render.yaml`](../render.yaml) at the repo root:
   - Service: `ai-voice-api`
   - Region: **Singapore** (`singapore`)
   - Root directory: `apps/api`
   - Auto-deploy: **on commit** to `main`
   - Health check path: `/health`
4. When prompted, set secret env vars (see below)
5. Deploy and note the URL: `https://ai-voice-api.onrender.com` (name may vary)

### Environment variables (Render Dashboard)

| Variable                    | Example / notes                                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `DATABASE_URL`              | Supabase **direct** connection string (port 5432)                                                                        |
| `SUPABASE_URL`              | `https://<project-ref>.supabase.co`                                                                                      |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (secret)                                                                                                |
| `CORS_ORIGINS`              | `http://localhost:3000,https://yourdomain.ai,https://app.yourdomain.ai,https://www.yourdomain.ai` (+ Vercel preview URL) |
| `LOG_LEVEL`                 | `INFO` (default in blueprint)                                                                                            |

`PORT` is set automatically by Render — do not override.

## 2. Verify deployment

```bash
# Replace with your Render URL
export API_URL=https://ai-voice-api.onrender.com

curl -sS -w "\nHTTP %{http_code} time %{time_total}s\n" "$API_URL/health"
curl -sS "$API_URL/"
```

Expected `/health` response:

```json
{
  "status": "ok",
  "timestamp": "2026-05-31T12:00:00Z",
  "database": "ok"
}
```

- Status **200**
- Response time **under 200ms** when the service is already warm
- Logs appear in Render → **Logs** (JSON structlog lines)

## 3. Warm-ping cron (cron-job.org)

Render free web services **sleep after ~15 minutes** of no traffic. Voice webhooks need the API awake.

1. Sign up at [cron-job.org](https://cron-job.org) (free tier is enough)
2. **Create cronjob**
   - Title: `AI Voice API warm ping`
   - URL: `https://<your-render-host>/health`
   - Schedule: every **10 minutes** (`*/10 * * * *`)
   - Request method: **GET**
   - Expected status: **200**
3. Save and enable the job
4. Open **History** after 10–20 minutes and confirm successful runs

This adds ~4,300 requests/month — within typical free-tier limits (see [design.md](./design.md#free-tier-survival-notes)).

### Optional: measure latency after idle

After 30+ minutes without manual traffic (cron still running, service should stay warm):

```bash
curl -sS -w "time_total=%{time_total}s\n" -o /dev/null "$API_URL/health"
```

Target: **&lt; 200ms** when warm. First request after a cold start can take 30s+ on free tier — that is why the cron exists.

## 4. Auto-deploy from `main`

With `autoDeployTrigger: commit` in `render.yaml`, each push to `main` triggers a new deploy after the previous one finishes.

Verify:

1. Merge a small change to `main`
2. Render → **Events** shows a new deploy
3. `/health` still returns 200 after deploy completes

## 5. Wire the frontend

Set in Vercel (see **[docs/deploy-vercel.md](../docs/deploy-vercel.md)** — ticket 1.18):

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.ai
# or https://ai-voice-ocy9.onrender.com before custom api. domain
```

Add all Vercel production URLs to `CORS_ORIGINS` on Render.

## Troubleshooting

| Symptom                     | Fix                                                                      |
| --------------------------- | ------------------------------------------------------------------------ |
| `/health` returns 500       | Check `DATABASE_URL` (direct connection, not pooler on 6543 for asyncpg) |
| Deploy fails build          | Confirm `rootDir: apps/api` and Python 3.11                              |
| Service sleeps despite cron | Confirm cron URL is exact `/health`, schedule every 10 min, job enabled  |
| CORS errors from browser    | Add frontend origin to `CORS_ORIGINS` on Render                          |

## Acceptance checklist (1.17)

- [ ] FastAPI accessible at production Render URL
- [ ] Auto-deploy works on push to `main`
- [ ] cron-job.org hits `/health` every 10 minutes (history shows 200)
- [ ] `/health` responds in under 200ms when warm
- [ ] Logs visible in Render dashboard
