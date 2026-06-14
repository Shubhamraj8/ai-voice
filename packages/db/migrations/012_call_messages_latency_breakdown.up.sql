-- Ticket 2.15 — per-turn latency breakdown (STT/LLM/TTS components).
-- ``latency_ms`` already stores the total; this JSONB stores the segments,
-- e.g. {"stt_ms": 120, "llm_ms": 340, "tts_first_byte_ms": 210, "total_ms": 780}.
ALTER TABLE call_messages ADD COLUMN latency_breakdown jsonb;
