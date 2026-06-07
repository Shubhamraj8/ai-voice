# Deepgram Aura-1 Voice Catalogue

> Referenced by ticket 2.07 — for use in the Phase 3 agent-edit form.

Deepgram Aura-1 is the TTS engine used for the **India English**, **US English**, and **Global English** markets.
It bills at **$0.015 / 1 000 characters** synthesized.

---

## Concise-reply budget

The pipeline enforces ≤ 25 words (~150 chars) per turn to keep TTS latency and cost low.

| Metric              | Target          |
| ------------------- | --------------- |
| Words per turn      | ≤ 25            |
| Characters per turn | ≤ 150 (approx.) |
| Cost per turn       | ≤ $0.0023       |
| TTFB p95            | ≤ 350 ms        |

---

## Audio configuration

| Parameter      | Value      | Notes                                   |
| -------------- | ---------- | --------------------------------------- |
| Encoding       | `linear16` | 16-bit signed PCM, little-endian        |
| Sample rate    | `8000 Hz`  | Matches Twilio `<Stream>` media format  |
| Channels       | 1 (mono)   |                                         |
| Retry attempts | 3          | Exponential back-off: 0.5 s → 1 s → 2 s |

---

## Voice catalogue

All voices are Deepgram Aura-1 models. Use the `voice_id` string verbatim in API calls and tenant configs.

| `voice_id`        | Gender | Accent       | Character            | Recommended for        |
| ----------------- | ------ | ------------ | -------------------- | ---------------------- |
| `aura-asteria-en` | F      | 🇮🇳 Indian-EN | Warm, clear          | **Default** (India EN) |
| `aura-luna-en`    | F      | 🇺🇸 American  | Calm, friendly       | US English support     |
| `aura-stella-en`  | F      | 🇺🇸 American  | Warm, expressive     | US English sales       |
| `aura-athena-en`  | F      | 🇬🇧 British   | Authoritative        | Global English tier    |
| `aura-hera-en`    | F      | 🇺🇸 American  | Professional         | US business calls      |
| `aura-orion-en`   | M      | 🇺🇸 American  | Deep, confident      | US English support     |
| `aura-arcas-en`   | M      | 🇺🇸 American  | Casual, approachable | Informal bots          |
| `aura-perseus-en` | M      | 🇺🇸 American  | Crisp, clear         | Concise call flows     |
| `aura-angus-en`   | M      | 🇮🇪 Irish     | Friendly, warm       | Global English alt     |
| `aura-orpheus-en` | M      | 🇺🇸 American  | Clear, neutral       | US fallback            |
| `aura-helios-en`  | M      | 🇬🇧 British   | Warm, trustworthy    | UK / Global markets    |
| `aura-zeus-en`    | M      | 🇺🇸 American  | Authoritative        | Premium US tier        |

---

## Setting a voice for a tenant

Voice selection is stored per-agent in the `agents` table (Phase 3 agent-edit form).
For now, override via the pipeline or pass `voice_id` to `synthesize()`:

```python
from app.providers.deepgram_tts import DeepgramTTS

tts = DeepgramTTS()
async for chunk in tts.synthesize(
    text="Hello, how can I help you today?",
    voice_id="aura-asteria-en",   # or any voice from the catalogue above
    language="en",
):
    ...  # stream PCM bytes to Twilio
```

---

## Switching a tenant's TTS voice (Phase 3)

When the agent-edit form is implemented, the `voice_id` will be stored on the `agents` row and forwarded through the pipeline. Until then, the provider defaults to `aura-asteria-en`.

---

## Cost estimation

```
cost_usd = len(text) * 0.015 / 1000
```

This is logged as `cost_usd` in every `deepgram_tts.synthesized` structured log event.

---

## Metrics logged per synthesis call

Every call to `DeepgramTTS.synthesize()` emits a `deepgram_tts.synthesized` structlog event with:

| Field       | Type  | Description                                |
| ----------- | ----- | ------------------------------------------ |
| `voice_id`  | str   | Model used                                 |
| `tts_chars` | int   | Character count synthesized (billing unit) |
| `ttfb_ms`   | int   | Time-to-first-byte in milliseconds         |
| `total_ms`  | int   | Total synthesis duration in milliseconds   |
| `attempt`   | int   | Retry attempt number (1 = first try)       |
| `cost_usd`  | float | Estimated cost for this synthesis call     |

---

## API reference

- Deepgram Speak WebSocket API: https://developers.deepgram.com/reference/text-to-speech-api
- Aura-1 model overview: https://deepgram.com/product/text-to-speech
- SDK: `deepgram-sdk >= 7.0.0` (PyPI) — uses the REST Speak streaming API (`AsyncDeepgramClient.speak.v1.audio.generate`)
