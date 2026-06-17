ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_transfer_to_number_e164;
ALTER TABLE agents DROP COLUMN IF EXISTS transfer_to_number;
