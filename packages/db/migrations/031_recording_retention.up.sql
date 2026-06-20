-- Ticket 5.15 — 30-day recording retention.
-- Records when a call's audio was purged from Storage (the transcript stays).

ALTER TABLE calls ADD COLUMN IF NOT EXISTS recording_deleted_at timestamptz;
