"""Tests for LLM provider selection (DeepSeek/Gemini). Pure helpers, no pipecat."""

from types import SimpleNamespace

from app.config import llm_key_present, selected_llm_provider
from app.services.calls import build_provider_snapshot
from app.services.cost_calculator import llm_cost


def _settings(**over):
    base = dict(
        llm_provider="deepseek",
        gemini_api_key="",
        deepseek_api_key="",
        deepgram_api_key="",
    )
    base.update(over)
    return SimpleNamespace(**base)


def test_selected_provider_defaults_to_deepseek():
    assert selected_llm_provider(_settings()) == "deepseek"
    assert selected_llm_provider(_settings(llm_provider="gemini")) == "gemini"
    assert selected_llm_provider(_settings(llm_provider="GOOGLE")) == "gemini"


def test_llm_key_present_per_provider():
    assert llm_key_present(_settings(deepseek_api_key="x")) is True
    assert llm_key_present(_settings(deepseek_api_key="")) is False
    assert llm_key_present(_settings(llm_provider="gemini", gemini_api_key="g")) is True
    assert llm_key_present(_settings(llm_provider="gemini", gemini_api_key="")) is False


def test_provider_snapshot_records_selected_llm():
    deepseek = build_provider_snapshot(
        _settings(deepgram_api_key="d", deepseek_api_key="k")
    )
    assert deepseek["llm"] == "deepseek_native"

    gemini = build_provider_snapshot(
        _settings(deepgram_api_key="d", llm_provider="gemini", gemini_api_key="g")
    )
    assert gemini["llm"] == "gemini"

    # Deepgram present but no LLM key → STT+TTS only (no llm recorded).
    deepgram_only = build_provider_snapshot(_settings(deepgram_api_key="d"))
    assert deepgram_only["llm"] is None


def test_llm_cost_handles_gemini():
    assert llm_cost("gemini", 4000) > 0
    assert llm_cost("deepseek_native", 4000) > 0
    assert llm_cost("gemini", 0) == 0.0
    assert llm_cost(None, 4000) == 0.0
