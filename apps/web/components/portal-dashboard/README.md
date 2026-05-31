# Client portal module

Navigation shell and placeholder pages for ticket **1.15**.

Edit files here only — routes under `app/(portal)/` are thin wrappers.

## Structure

| File                           | Purpose                             |
| ------------------------------ | ----------------------------------- |
| `portal-shell.tsx`             | Layout shell with mobile drawer     |
| `portal-sidebar.tsx`           | Sidebar nav with active state       |
| `portal-user-menu.tsx`         | Header dropdown + sign out          |
| `portal-dashboard-content.tsx` | Dashboard coming-soon + /me context |
| `placeholder-page.tsx`         | Shared coming-soon page             |
| `nav.ts`                       | Nav items and default path          |

## Routes

- `/portal` → redirects to `/portal/dashboard`
- `/portal/dashboard`, `/portal/calls`, `/portal/knowledge`, `/portal/settings`

## API

User and tenant info comes from `GET /me` via `lib/api/me.ts` (requires `NEXT_PUBLIC_API_URL`).
