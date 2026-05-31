# Internal dashboard module

Navigation shell and placeholder pages for ticket **1.16**.

Edit files here only — routes under `app/(internal)/` are thin wrappers.

## Structure

| File                     | Purpose                         |
| ------------------------ | ------------------------------- |
| `internal-shell.tsx`     | Layout shell with mobile drawer |
| `internal-sidebar.tsx`   | Sidebar nav with active state   |
| `internal-user-menu.tsx` | Header dropdown + sign out      |
| `placeholder-page.tsx`   | Shared coming-soon page         |
| `nav.ts`                 | Nav items and default path      |
| `index.css`              | Violet internal accent theme    |

## Routes

- `/internal` → redirects to `/internal/tenants`
- `/internal/tenants`, `/internal/calls`, `/internal/audit-log`, `/internal/metrics`
