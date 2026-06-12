-- Ticket 2.13 — per-turn TTS character count for Phase 4 cost calculation.
ALTER TABLE call_messages ADD COLUMN tts_chars int;

-- Ordered transcript reads for a single call (oldest-first).
CREATE INDEX call_messages_call_id_created_at_idx
  ON call_messages (call_id, created_at);

-- Timeout job: quickly find calls that are still open (never closed by a
-- status callback) so the reaper can close them.
CREATE INDEX calls_open_idx ON calls (started_at) WHERE ended_at IS NULL;
