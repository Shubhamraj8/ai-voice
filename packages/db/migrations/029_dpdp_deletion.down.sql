DROP TABLE IF EXISTS dpdp_deletion_requests;

ALTER TABLE tenants DROP COLUMN IF EXISTS deletion_blocked;
ALTER TABLE tenants DROP COLUMN IF EXISTS deleted_at;
