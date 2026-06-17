"""Tests for per-call cost calculation (ticket 4.14). DB mocked."""

import json
import uuid

from app.services import cost_calculator as cc

# --- pure formulas -----------------------------------------------------------


def test_stt_cost_deepgram():
    assert cc.stt_cost("deepgram", 120) == 120 / 60 * cc.DEEPGRAM_STT_PER_MIN


def test_stt_cost_other_provider_is_zero():
    assert cc.stt_cost("cartesia", 120) == 0.0
    assert cc.stt_cost("deepgram", None) == 0.0


def test_tts_cost_is_per_character():
    assert cc.tts_cost("deepgram", 1000) == cc.DEEPGRAM_TTS_PER_1K_CHARS
    assert cc.tts_cost("deepgram", 0) == 0.0


def test_telephony_cost():
    assert cc.telephony_cost(60) == cc.TWILIO_INDIA_INBOUND_PER_MIN


def test_llm_cost_estimated_from_transcript():
    # deepseek provider → estimate; non-deepseek → 0
    assert cc.llm_cost("deepseek_native", 4000) > 0
    assert cc.llm_cost("other", 4000) == 0.0


# --- compute_and_store_cost --------------------------------------------------


async def test_compute_and_store_writes_breakdown(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(cc, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {
        "duration_secs": 120,
        "provider_snapshot": json.dumps(
            {"stt": "deepgram", "tts": "deepgram", "llm": "deepseek_native"}
        ),
    }
    conn.fetchval.side_effect = [1000, 800]  # tts_chars, transcript_chars
    call_id = uuid.uuid4()

    await cc.compute_and_store_cost(call_id)

    conn.execute.assert_awaited_once()
    args = conn.execute.await_args.args
    assert args[1] == call_id
    assert args[2] == round(120 / 60 * cc.DEEPGRAM_STT_PER_MIN, 5)  # stt
    assert args[3] == round(1000 / 1000 * cc.DEEPGRAM_TTS_PER_1K_CHARS, 5)  # tts
    assert args[5] == round(120 / 60 * cc.TWILIO_INDIA_INBOUND_PER_MIN, 5)  # telephony
    # total == sum of the four components
    assert args[6] == round(args[2] + args[3] + args[4] + args[5], 5)


async def test_compute_handles_dict_snapshot(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(cc, "get_pool", lambda: pool)
    # provider_snapshot already a dict (codec registered) — must still work.
    conn.fetchrow.return_value = {
        "duration_secs": 60,
        "provider_snapshot": {"stt": "deepgram", "tts": "deepgram", "llm": None},
    }
    conn.fetchval.side_effect = [500, 400]

    await cc.compute_and_store_cost(uuid.uuid4())

    args = conn.execute.await_args.args
    assert args[4] == 0.0  # llm None → no LLM cost


async def test_compute_missing_call_is_noop(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(cc, "get_pool", lambda: pool)
    conn.fetchrow.return_value = None

    await cc.compute_and_store_cost(uuid.uuid4())

    conn.execute.assert_not_awaited()
