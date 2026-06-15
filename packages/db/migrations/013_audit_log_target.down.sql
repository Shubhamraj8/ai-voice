DROP INDEX IF EXISTS audit_log_target_idx;
ALTER TABLE audit_log DROP COLUMN IF EXISTS target_id;
ALTER TABLE audit_log DROP COLUMN IF EXISTS target_type;
