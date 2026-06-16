-- Ticket 4.06 — per-turn RAG retrieval metrics on assistant turns.
ALTER TABLE call_messages ADD COLUMN IF NOT EXISTS retrieval_meta jsonb;
