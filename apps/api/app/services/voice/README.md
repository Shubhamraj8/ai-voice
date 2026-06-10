# Voice pipeline (tickets 2.10–2.12)

The Twilio ↔ Pipecat pipeline lives in `pipeline.py`.

## Full conversation pipeline (2.12)

When both `DEEPGRAM_API_KEY` and `DEEPSEEK_API_KEY` are set:

```
transport.input → Silero VAD → Deepgram STT → UserTurnProcessor → LLM user aggregator → DeepSeek LLM → Deepgram TTS → buffer monitor → transport.output → LLM assistant aggregator
```

Conversation settings are in `conversation_config.py`. Per-turn logs
(`conversation_turn_complete`) are emitted from `turn_logger.py` with
`user_input`, `assistant_output`, `stt_ms`, `llm_ms`, `tts_first_byte_ms`,
`total_ms`, and `tts_chars`.

## Deepgram-only fallback (2.10, 2.11)

When only `DEEPGRAM_API_KEY` is set:

```
transport.input → Silero VAD → Deepgram STT → UserTurnProcessor → Deepgram TTS → buffer monitor → transport.output
```

## Conversation parameters (2.12)

| Parameter                 | Default             | Location                 | Purpose                                   |
| ------------------------- | ------------------- | ------------------------ | ----------------------------------------- |
| `SYSTEM_PROMPT`           | receptionist prompt | `conversation_config.py` | Hardcoded agent persona for dev calls     |
| `MAX_CONVERSATION_TURNS`  | `10`                | `conversation_config.py` | User+assistant pairs kept in LLM context  |
| `MAX_LLM_OUTPUT_TOKENS`   | `200`               | `conversation_config.py` | Concise reply budget for TTS cost control |
| `CONNECT_GREETING_PROMPT` | connect greeting    | `conversation_config.py` | Synthetic first user message on connect   |

## VAD / turn parameters (2.10, 2.11)

| Parameter                    | Default  | Location         | Purpose                                                                                       |
| ---------------------------- | -------- | ---------------- | --------------------------------------------------------------------------------------------- |
| `VAD_CONFIDENCE`             | `0.65`   | `turn_config.py` | Silero speech confidence threshold. Lowered slightly for Indian-accent telephony.             |
| `VAD_START_SECS`             | `0.25`   | `turn_config.py` | Seconds of speech before VAD confirms start (reduces noise false-positives).                  |
| `VAD_STOP_SECS`              | `0.25`   | `turn_config.py` | Seconds of silence before VAD confirms stop. Brief intra-sentence pauses stay below turn-end. |
| `VAD_MIN_VOLUME`             | `0.55`   | `turn_config.py` | Minimum RMS volume for speech detection on 8 kHz phone audio.                                 |
| `USER_TURN_END_TIMEOUT_SECS` | `0.8`    | `turn_config.py` | Policy floor after VAD silence before the user turn ends (~800 ms).                           |
| `DEEPGRAM_ENDPOINTING_MS`    | `300`    | `turn_config.py` | Deepgram utterance boundary (ms). Matches provider layer.                                     |
| `DEEPGRAM_STT_MODEL`         | `nova-3` | `turn_config.py` | Nova-3 monolingual English STT.                                                               |
| `vad_events`                 | `true`   | `pipeline.py`    | Deepgram speech-started / utterance-end events for turn detection.                            |
| `smart_format`               | `true`   | `pipeline.py`    | Punctuation and formatting on transcripts.                                                    |

## Barge-in (2.11)

`VADUserTurnStartStrategy(enable_interruptions=True)` emits an
`InterruptionFrame` when the caller speaks during agent playback. Pipecat's
`DeepgramTTSService` handles this by sending a `Clear` message on the TTS
WebSocket, stopping billed character streaming and discarding pending audio.

## Adjusting for your callers

- **Premature agent responses**: increase `USER_TURN_END_TIMEOUT_SECS` (e.g. `1.0`) or `VAD_STOP_SECS`.
- **Slow turn-end**: decrease `USER_TURN_END_TIMEOUT_SECS` (e.g. `0.6`) — stay under 1 s per acceptance criteria.
- **Missed barge-in**: lower `VAD_CONFIDENCE` or `VAD_MIN_VOLUME`.
- **False barge-in from background noise**: raise `VAD_CONFIDENCE` or `VAD_START_SECS`.
