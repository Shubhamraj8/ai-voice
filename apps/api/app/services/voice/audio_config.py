"""Audio sample rates and encoding for the Twilio ↔ Deepgram voice path (ticket 2.05).

Twilio Media Streams carry 8 kHz μ-law (G.711) in both directions. Pipecat's
``TwilioFrameSerializer`` converts that wire format to linear16 PCM at the
pipeline rates configured below:

  Caller → Twilio (μ-law 8 kHz)
         → serializer deserializes to PCM at ``STT_INPUT_SAMPLE_RATE`` (16 kHz)
         → Deepgram STT (linear16)

  Deepgram TTS (linear16 at ``TTS_OUTPUT_SAMPLE_RATE``, 8 kHz)
         → serializer serializes to μ-law 8 kHz
         → Twilio → caller

Keeping TTS at 8 kHz avoids an extra downsample before the Twilio serializer.
Resampling from 8 kHz to 16 kHz on ingress is handled inside the serializer.
"""

TWILIO_SAMPLE_RATE = 8000
STT_INPUT_SAMPLE_RATE = 16000
TTS_OUTPUT_SAMPLE_RATE = 8000
AUDIO_CHANNELS = 1
PCM_SAMPLE_WIDTH_BYTES = 2
