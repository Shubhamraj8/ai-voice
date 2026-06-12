DROP INDEX IF EXISTS calls_open_idx;
DROP INDEX IF EXISTS call_messages_call_id_created_at_idx;
ALTER TABLE call_messages DROP COLUMN IF EXISTS tts_chars;
