# Per-turn latency schema (ticket 2.15)

Every assistant turn records its latency so bottlenecks can be diagnosed.

## Storage — `call_messages`

| Column              | Type    | Meaning                                                       |
| ------------------- | ------- | ------------------------------------------------------------- |
| `latency_ms`        | `int`   | Total user-speech-end → bot-audio-start latency for the turn. |
| `latency_breakdown` | `jsonb` | Per-segment components (see below). Null on user-role rows.   |

`latency_breakdown` shape:

```json
{
  "stt_ms": 120, // STT time-to-final
  "llm_ms": 340, // LLM time-to-first-token (or processing time)
  "tts_first_byte_ms": 210, // TTS time-to-first-audio-byte
  "total_ms": 780 // mirrors latency_ms
}
```

Any component may be `null` when the underlying Pipecat metric was unavailable
for that turn. The values come from the pipeline's `UserBotLatencyObserver`
(time-to-first-byte per processor) and usage/processing metrics, assembled in
[`turn_logger.py`](../apps/api/app/services/voice/turn_logger.py).

## Slow-turn warning

A turn whose `total_ms` exceeds `SLOW_TURN_THRESHOLD_MS` (1500 ms) emits a
`slow_turn` warning log with the full breakdown.

## Internal endpoint

`GET /internal/latency` (internal-auth) returns p50/p95/p99 for each segment
over the most recent 100 assistant turns:

```json
{
  "sample_size": 100,
  "stt_ms": { "p50": 110, "p95": 180, "p99": 240 },
  "llm_ms": { "p50": 320, "p95": 600, "p99": 850 },
  "tts_first_byte_ms": { "p50": 200, "p95": 300, "p99": 360 },
  "total_ms": { "p50": 700, "p95": 1100, "p99": 1500 }
}
```

Percentiles are linear-interpolated; see
[`metrics.py`](../apps/api/app/services/metrics.py).
