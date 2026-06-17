-- Ticket 4.13 — post-call summary fields + canonical outcome vocabulary.

ALTER TABLE calls ADD COLUMN IF NOT EXISTS intent text;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS summary_generated_at timestamptz;

-- Adopt the 4.13 outcome vocabulary; map legacy values first so the new CHECK
-- doesn't reject existing rows.
UPDATE calls SET outcome = 'resolved' WHERE outcome = 'booked';
UPDATE calls SET outcome = 'other' WHERE outcome = 'info_only';

ALTER TABLE calls DROP CONSTRAINT IF EXISTS calls_outcome_check;
ALTER TABLE calls ADD CONSTRAINT calls_outcome_check CHECK (
  outcome IS NULL
  OR outcome IN ('resolved', 'transferred', 'escalated', 'abandoned', 'other')
);
