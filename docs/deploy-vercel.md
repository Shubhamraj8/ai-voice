# Vercel deployment + domain (ticket 1.18)

Deploy the Next.js app to [Vercel](https://vercel.com) and wire custom domains with subdomain routing.

**Backend stays on Render** — see [deploy-render.md](./deploy-render.md) (ticket 1.17).

## Architecture

| Host                     | Serves                      | Where                               |
| ------------------------ | --------------------------- | ----------------------------------- |
| `yourdomain.ai` / `www`  | Marketing landing           | Vercel                              |
| `app.yourdomain.ai`      | Client portal               | Vercel (middleware → `/portal/*`)   |
| `internal.yourdomain.ai` | Internal dashboard          | Vercel (middleware → `/internal/*`) |
| `api.yourdomain.ai`      | FastAPI `/health`, `/me`, … | **Render** (DNS CNAME, not Vercel)  |

## Prerequisites

- Render API deployed and warm (ticket 1.17)
- Domain registered (e.g. `yourdomain.ai`)
- Supabase project with auth configured

## 1. Create the Vercel project

1. [Vercel Dashboard](https://vercel.com/new) → **Import** `Shubhamraj8/ai-voice`
2. **Root Directory:** `apps/web` → Edit → set to `apps/web`
3. **Framework:** Next.js (auto-detected)
4. Build settings read from [`apps/web/vercel.json`](../apps/web/vercel.json):
   - Install: `cd ../.. && pnpm install --frozen-lockfile`
   - Build: `cd ../.. && pnpm --filter @ai-voice/web build`
5. Enable **Include source files outside of the Root Directory** (required for pnpm monorepo)
6. **Production branch:** `main` → auto-deploy on push

## 2. Environment variables (Vercel)

Project → **Settings** → **Environment Variables** (Production + Preview):

| Variable                        | Value                                                               |
| ------------------------------- | ------------------------------------------------------------------- |
| `NEXT_PUBLIC_SUPABASE_URL`      | `https://<project-ref>.supabase.co`                                 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key                                                   |
| `NEXT_PUBLIC_API_URL`           | `https://api.yourdomain.ai` or `https://ai-voice-ocy9.onrender.com` |
| `NEXT_PUBLIC_APP_DOMAIN`        | `yourdomain.ai`                                                     |
| `NEXT_PUBLIC_PORTAL_HOST`       | `app.yourdomain.ai`                                                 |
| `NEXT_PUBLIC_INTERNAL_HOST`     | `internal.yourdomain.ai` (optional)                                 |

Copy from [`apps/web/.env.example`](../apps/web/.env.example).

After first deploy, update **Render** `CORS_ORIGINS` to include:

```
http://localhost:3000,https://yourdomain.ai,https://www.yourdomain.ai,https://app.yourdomain.ai,https://internal.yourdomain.ai,https://<project>.vercel.app
```

## 3. Custom domains (Vercel)

Project → **Settings** → **Domains** → add:

| Domain                   | Purpose                           |
| ------------------------ | --------------------------------- |
| `yourdomain.ai`          | Apex — marketing                  |
| `www.yourdomain.ai`      | Redirect to apex (Vercel default) |
| `app.yourdomain.ai`      | Client portal subdomain           |
| `internal.yourdomain.ai` | Internal ops subdomain (optional) |

Vercel issues TLS certificates automatically once DNS verifies.

### DNS records (at your registrar)

**Vercel (frontend):**

| Type  | Name       | Value                                              |
| ----- | ---------- | -------------------------------------------------- |
| A     | `@`        | `76.76.21.21` (Vercel apex — confirm in Vercel UI) |
| CNAME | `www`      | `cname.vercel-dns.com`                             |
| CNAME | `app`      | `cname.vercel-dns.com`                             |
| CNAME | `internal` | `cname.vercel-dns.com`                             |

Use exact values shown in Vercel → Domains for your project.

**Render (API) — separate from Vercel:**

| Type  | Name  | Value                                           |
| ----- | ----- | ----------------------------------------------- |
| CNAME | `api` | `ai-voice-ocy9.onrender.com` (your Render host) |

Then set `NEXT_PUBLIC_API_URL=https://api.yourdomain.ai` on Vercel and redeploy.

Verify:

```bash
curl -sS https://api.yourdomain.ai/health
```

## 4. Supabase Auth redirect URLs

Supabase → **Authentication** → **URL Configuration**:

| Setting       | URLs to add                                                                                                             |
| ------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Site URL      | `https://app.yourdomain.ai`                                                                                             |
| Redirect URLs | `https://app.yourdomain.ai/auth/callback`, `https://yourdomain.ai/auth/callback`, `http://localhost:3000/auth/callback` |

Add Vercel preview URLs if needed: `https://*.vercel.app/auth/callback`

## 5. Subdomain routing (in repo)

[`apps/web/lib/auth/host-routing.ts`](../apps/web/lib/auth/host-routing.ts) + middleware:

- `app.*` → rewrites to `/portal/*` (e.g. `app.domain/` → dashboard)
- `internal.*` → rewrites to `/internal/*`
- Apex `/portal/*` → redirects to `app.*` when `NEXT_PUBLIC_PORTAL_HOST` is set

Local dev unchanged: use `http://localhost:3000/portal`, etc.

## 6. Verify deployment

| Check                                        | Expected                                   |
| -------------------------------------------- | ------------------------------------------ |
| `https://yourdomain.ai`                      | Marketing landing page                     |
| `https://app.yourdomain.ai`                  | Portal (login redirect if unauthenticated) |
| `https://app.yourdomain.ai/portal/dashboard` | Portal dashboard after login               |
| `https://api.yourdomain.ai/health`           | `200`, `"database":"ok"`                   |
| Push to `main`                               | Vercel production deploy triggers          |

```powershell
# From repo root after deploy
curl -sS https://yourdomain.ai
curl -sS https://app.yourdomain.ai/login
curl -sS https://api.yourdomain.ai/health
```

## Troubleshooting

| Symptom                | Fix                                                           |
| ---------------------- | ------------------------------------------------------------- |
| Build fails on Vercel  | Confirm Root Directory = `apps/web`, monorepo include enabled |
| Portal CORS errors     | Add Vercel URLs to Render `CORS_ORIGINS`                      |
| Auth redirect loop     | Add callback URLs in Supabase                                 |
| `app.` shows marketing | Confirm domain added in Vercel + DNS propagated               |
| API 404 on Vercel      | `api.` must point to **Render**, not Vercel                   |

## Acceptance checklist (1.18)

- [ ] Apex domain shows marketing site
- [ ] `app.yourdomain.ai` shows portal (after login)
- [ ] `api.yourdomain.ai/health` returns 200
- [ ] TLS valid on all subdomains
- [ ] Auto-deploy fires on push to `main`
