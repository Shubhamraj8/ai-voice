DROP TABLE IF EXISTS escalations;

ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_escalation_sms_e164;
ALTER TABLE tenants DROP COLUMN IF EXISTS escalation_sms;
ALTER TABLE tenants DROP COLUMN IF EXISTS escalation_email;
