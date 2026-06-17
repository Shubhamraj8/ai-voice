UPDATE calls SET outcome = 'booked' WHERE outcome = 'resolved';
UPDATE calls SET outcome = 'info_only' WHERE outcome IN ('escalated', 'other');

ALTER TABLE calls DROP CONSTRAINT IF EXISTS calls_outcome_check;
ALTER TABLE calls ADD CONSTRAINT calls_outcome_check CHECK (
  outcome IS NULL OR outcome IN ('booked', 'transferred', 'info_only', 'abandoned')
);

ALTER TABLE calls DROP COLUMN IF EXISTS summary_generated_at;
ALTER TABLE calls DROP COLUMN IF EXISTS intent;
