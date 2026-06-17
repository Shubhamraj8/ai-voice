-- Ticket 4.14 — per-call COGS breakdown.
ALTER TABLE calls ADD COLUMN IF NOT EXISTS cost_stt_usd numeric(10, 5);
ALTER TABLE calls ADD COLUMN IF NOT EXISTS cost_tts_usd numeric(10, 5);
ALTER TABLE calls ADD COLUMN IF NOT EXISTS cost_llm_usd numeric(10, 5);
ALTER TABLE calls ADD COLUMN IF NOT EXISTS cost_telephony_usd numeric(10, 5);
ALTER TABLE calls ADD COLUMN IF NOT EXISTS cost_total_usd numeric(10, 5);
