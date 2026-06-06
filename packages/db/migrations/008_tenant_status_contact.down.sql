DROP INDEX IF EXISTS tenants_status_idx;

ALTER TABLE tenants
  DROP CONSTRAINT IF EXISTS tenants_status_check;

ALTER TABLE tenants
  DROP COLUMN IF EXISTS contact_phone,
  DROP COLUMN IF EXISTS contact_name,
  DROP COLUMN IF EXISTS contact_email,
  DROP COLUMN IF EXISTS status;
