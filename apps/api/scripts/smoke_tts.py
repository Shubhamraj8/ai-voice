#!/usr/bin/env python
"""Manual smoke-test for DeepgramTTS (ticket 2.07).

Usage
-----
1. Set your Deepgram API key in .env:
       DEEPGRAM_API_KEY=your_key_here

2. Run from apps/api/:
       python scripts/smoke_tts.py

3. Optional: pass a custom text and voice:
       python scripts/smoke_tts.py "Your custom text here" aura-zeus-en

The script will:
  - Synthesize the text (default: canonical greeting)
  - Print TTFB, total_ms, tts_chars, and cost_usd
  - Save the raw PCM bytes to /tmp/tts_output.pcm
  - Print instructions for playing the audio

Requirements
------------
  - Deepgram API key in .env (DEEPGRAM_API_KEY)
  - deepgram-sdk >= 7.0.0  (installed via pip install deepgram-sdk)
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# Make sure the app package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from app.providers.deepgram_tts import VOICE_CATALOGUE, DeepgramTTS  # noqa: E402

_DEFAULT_TEXT = "Hello, how can I help you today?"
_OUTPUT_PATH = Path(__file__).resolve().parent / "tts_output.pcm"


async def main(text: str, voice_id: str) -> None:
    print("\n🎙️  DeepgramTTS smoke-test")
    print(f"   Voice  : {voice_id}")
    print(f"   Text   : {text!r} ({len(text)} chars)")
    print(f"   Budget : {'✅ OK' if len(text.split()) <= 25 else '⚠️  OVER 25 words'}")
    print()

    tts = DeepgramTTS()
    chunks: list[bytes] = []
    t_start = time.monotonic()
    t_first_byte: float | None = None

    async for chunk in tts.synthesize(text, voice_id=voice_id, language="en"):
        if t_first_byte is None:
            t_first_byte = time.monotonic()
            ttfb_ms = round((t_first_byte - t_start) * 1000)
            print(f"   ⚡ First byte received in {ttfb_ms} ms")
        chunks.append(chunk)

    t_end = time.monotonic()
    total_ms = round((t_end - t_start) * 1000)
    total_bytes = sum(len(c) for c in chunks)
    cost_usd = round(len(text) * 0.015 / 1000, 6)

    # Save PCM
    _OUTPUT_PATH.write_bytes(b"".join(chunks))

    print("   ✅ Synthesis complete")
    print(f"   Total time : {total_ms} ms")
    duration_s = total_bytes // 2 / 8000
    print(
        f"   Audio size : {total_bytes:,} bytes "
        f"({duration_s:.2f}s @ 8kHz 16-bit mono)"
    )
    print(f"   tts_chars  : {len(text)}")
    print(f"   Cost       : ${cost_usd:.6f}")
    print()
    print(f"   PCM saved  : {_OUTPUT_PATH}")
    print()
    print("   To play (requires sox / ffplay):")
    print(f"     ffplay -f s16le -ar 8000 -ac 1 {_OUTPUT_PATH}")
    print(f"     play -r 8000 -e signed -b 16 -c 1 {_OUTPUT_PATH}")
    print()

    if t_first_byte and (t_first_byte - t_start) < 0.35:
        print("   ✅ TTFB < 350ms — latency target MET")
    else:
        print("   ⚠️  TTFB >= 350ms — latency target MISSED")


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_TEXT
    voice = sys.argv[2] if len(sys.argv) > 2 else "aura-asteria-en"

    if voice not in VOICE_CATALOGUE:
        print(f"❌ Unknown voice: {voice!r}")
        print(f"   Available: {', '.join(VOICE_CATALOGUE)}")
        sys.exit(1)

    asyncio.run(main(text, voice))
