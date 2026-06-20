-- Ticket 5.14 — per-tenant consent disclosure override.
-- Nullable: NULL means "use the standard disclosure line". Tenants in other
-- markets (or with reviewed wording) can override the spoken notice.

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS consent_disclosure_text text;
