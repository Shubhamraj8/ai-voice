-- Ticket 4.08 — human-transfer destination for the transferToHuman tool.
ALTER TABLE agents ADD COLUMN IF NOT EXISTS transfer_to_number text;

ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_transfer_to_number_e164;
ALTER TABLE agents ADD CONSTRAINT agents_transfer_to_number_e164 CHECK (
  transfer_to_number IS NULL OR transfer_to_number ~ '^\+[1-9]\d{1,14}$'
);
