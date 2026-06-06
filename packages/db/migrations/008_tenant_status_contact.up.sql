-- Ticket 3.01–3.03: tenant status, contact fields for internal dashboard.

ALTER TABLE tenants
  ADD COLUMN status text NOT NULL DEFAULT 'active',
  ADD COLUMN contact_email text,
  ADD COLUMN contact_name text,
  ADD COLUMN contact_phone text;

ALTER TABLE tenants
  ADD CONSTRAINT tenants_status_check CHECK (
    status IN ('active', 'paused', 'churned')
  );

CREATE INDEX tenants_status_idx ON tenants (status);

-- Backfill churned status from legacy archived_at rows.
UPDATE tenants
SET status = 'churned'
WHERE archived_at IS NOT NULL AND status = 'active';
