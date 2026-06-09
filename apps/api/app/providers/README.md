# Provider Abstraction Layer

> `app/providers/` — design.md §4

The voice pipeline never talks to Deepgram, Sarvam, or DeepSeek directly. It talks to three abstract interfaces. Concrete implementations are resolved at agent-spawn time from the tenant's `provider_config`.

---

## Package layout

```
app/providers/
├── __init__.py      # Public API — import from here
├── base.py          # STTProvider, TTSProvider, LLMProvider protocols + shared models
├── registry.py      # PROVIDERS dict + Pipeline dataclass + make_pipeline() factory
├── deepgram_stt.py  # Deepgram Nova-3 STT (ticket 2.08)
├── deepgram_tts.py  # Deepgram Aura-1 TTS (ticket 2.07)
├── deepseek_llm.py  # DeepSeek V4 Flash LLM (ticket 2.09)
└── stubs.py         # Stub classes for every concrete implementation
```

---

## The three protocols

| Protocol      | Method                                                        | Notes                   |
| ------------- | ------------------------------------------------------------- | ----------------------- |
| `STTProvider` | `connect(language)` → None                                    | Opens upstream WS       |
|               | `stream(audio_chunks)` → AsyncIterator[Transcript]            | Streaming transcription |
|               | `close()` → None                                              | Teardown                |
| `TTSProvider` | `synthesize(text, voice_id, language)` → AsyncIterator[bytes] | Streaming audio         |
| `LLMProvider` | `chat(messages, tools, max_tokens)` → LLMResponse             | Chat completion         |

Shared models: `Transcript`, `Message`, `ToolCall`, `LLMResponse`.

---

## Concrete implementations by market

| Market             | STT key        | TTS key        | LLM key             | Status                               |
| ------------------ | -------------- | -------------- | ------------------- | ------------------------------------ |
| **India English**  | `deepgram`     | `deepgram`     | `deepseek_native`   | ✅ STT+TTS+LLM LIVE (2.08/2.07/2.09) |
| **India Hindi**    | `sarvam`       | `sarvam`       | `deepseek_native`   | 🔜 Phase 3                           |
| **US English**     | `deepgram`     | `deepgram`     | `deepseek_native`   | ✅ STT+TTS+LLM LIVE (2.08/2.07/2.09) |
| **US HIPAA**       | `deepgram_baa` | `deepgram_baa` | `together_deepseek` | 🔜 Phase 3 (BAA required)            |
| **Global English** | `deepgram`     | `deepgram`     | `deepseek_native`   | ✅ STT+TTS+LLM LIVE (2.08/2.07/2.09) |

---

## How it works at runtime

```python
# In the Twilio voice webhook (ticket 2.07):
from app.providers import make_pipeline

pipeline = make_pipeline(tenant)   # resolves from tenant.provider_config
# pipeline.stt → DeepgramSTT()
# pipeline.tts → DeepgramTTS()
# pipeline.llm → DeepSeekNativeLLM()
```

`make_pipeline()` always creates **fresh instances** per call — never share a Pipeline across concurrent calls.

---

## Adding a new provider

1. Add a concrete class to `stubs.py` (or a new file if the impl is large).
2. Add the key → class mapping to `PROVIDERS` in `registry.py`.
3. Add the key to `VALID_PROVIDERS` (auto-derived from `PROVIDERS`).
4. Update `MARKET_DEFAULTS` if the provider is a default for a market.
5. Add tests in `tests/test_providers.py`.

---

## Switching a tenant's providers

Provider config lives on the `tenants` table as a JSONB column. Swapping a provider for a tenant is a database update, not a deploy:

```sql
UPDATE tenants
SET provider_config = '{"stt": "sarvam", "tts": "sarvam", "llm": "deepseek_native"}'
WHERE id = '<tenant-uuid>';
```

The next call that tenant receives will use the new provider. No restart needed.

---

## Phase implementation roadmap

| Phase             | Providers to implement                                                                    |
| ----------------- | ----------------------------------------------------------------------------------------- |
| Phase 2 (current) | `DeepgramSTT` (stub), **`DeepgramTTS` ✅ LIVE** (ticket 2.07), `DeepSeekNativeLLM` (stub) |
| Phase 3           | `SarvamSTT`, `SarvamTTS` (India Hindi market)                                             |
| Phase 3           | `DeepgramSTTEnterprise`, `DeepgramTTSEnterprise`, `TogetherDeepSeekLLM` (US HIPAA)        |
| Phase 4           | `OpenAIRealtimeSTT`, `OpenAITTS`, `ElevenLabsTTS`, `OpenAIGPT5MiniLLM`                    |

---

## Deepgram Nova-3 STT configuration

> Ticket 2.08 — streaming STT for India/US/Global English markets.

| Setting           | Value      | Notes                                      |
| ----------------- | ---------- | ------------------------------------------ |
| Model             | `nova-3`   | Monolingual English                        |
| Language          | `en`       | India English via Nova-3 monolingual model |
| Encoding          | `linear16` | PCM 16-bit                                 |
| Sample rate       | `16000` Hz | Matches Pipecat Twilio serializer output   |
| `smart_format`    | `true`     | Punctuation + formatting                   |
| `endpointing`     | `300` ms   | Utterance boundary detection               |
| `interim_results` | `true`     | Partial transcripts before finals          |
| `vad_events`      | `true`     | Speech-started / utterance-end events      |

Billing: **$0.0048 / minute** PAYG — confirm on first dev-call invoice.

---

## DeepSeek V4 Flash LLM configuration

> Ticket 2.09 — OpenAI-compatible native API for all v1 markets.

| Setting  | Default                    | Notes                                     |
| -------- | -------------------------- | ----------------------------------------- |
| Base URL | `https://api.deepseek.com` | OpenAI SDK compatible                     |
| Model    | `deepseek-v4-flash`        | Fast route for voice turns                |
| Timeout  | `30` s                     | Configurable via `DEEPSEEK_TIMEOUT_S`     |
| Caching  | Stable system prompt       | Repeat calls log `cached_tokens` in usage |

Billing (deepseek-v4-flash, per 1M tokens): cache hit $0.0028 · cache miss $0.14 · output $0.28.

---

## Deepgram Aura-1 Voice Catalogue

> Ticket 2.07 — for the Phase 3 agent-edit form. Bills at **$0.015 / 1 000 characters**.

Default voice: **`aura-asteria-en`** (Indian-English-friendly). Encoding: `linear16` @ 8 kHz (Twilio-compatible).

All 12 available voices:

| Voice ID          | Gender | Accent       |
| ----------------- | ------ | ------------ |
| `aura-asteria-en` | F      | Indian-EN 🇮🇳 |
| `aura-luna-en`    | F      | American 🇺🇸  |
| `aura-stella-en`  | F      | American 🇺🇸  |
| `aura-athena-en`  | F      | British 🇬🇧   |
| `aura-hera-en`    | F      | American 🇺🇸  |
| `aura-orion-en`   | M      | American 🇺🇸  |
| `aura-arcas-en`   | M      | American 🇺🇸  |
| `aura-perseus-en` | M      | American 🇺🇸  |
| `aura-angus-en`   | M      | Irish 🇮🇪     |
| `aura-orpheus-en` | M      | American 🇺🇸  |
| `aura-helios-en`  | M      | British 🇬🇧   |
| `aura-zeus-en`    | M      | American 🇺🇸  |
