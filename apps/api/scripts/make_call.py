"""
make_call.py — Twilio outbound call test (ticket 2.01)

Usage (from the repo root):
    # Load .env then run:
    python apps/api/scripts/make_call.py

Or set env vars manually on Windows:
    $env:TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    $env:TWILIO_AUTH_TOKEN  = "your_auth_token"
    $env:TWILIO_PHONE_NUMBER = "+91<your-twilio-number>"
    python apps/api/scripts/make_call.py
"""

import os
import sys

# ---------------------------------------------------------------------------
# Load .env from repo root if python-dotenv is available
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    # Walk up to find the repo root .env
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.abspath(os.path.join(_here, "..", "..", ".."))
    _env_path = os.path.join(_root, ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
        print(f"[info] Loaded env from {_env_path}")
except ImportError:
    pass  # python-dotenv not required; set vars manually

from twilio.rest import Client

# ---------------------------------------------------------------------------
# Credentials — always read from env, never hardcoded
# ---------------------------------------------------------------------------
ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")  # Your Twilio number

# The number to call — change this or pass as CLI arg: python make_call.py +91XXXXXXXXXX
TO_NUMBER = sys.argv[1] if len(sys.argv) > 1 else "+91XXXXXXXXXX"

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
missing = [
    k
    for k, v in {
        "TWILIO_ACCOUNT_SID": ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": AUTH_TOKEN,
        "TWILIO_PHONE_NUMBER": FROM_NUMBER,
    }.items()
    if not v
]

if missing:
    print(f"[error] Missing env vars: {', '.join(missing)}")
    print(
        "  Set TWILIO_PHONE_NUMBER to your purchased Twilio number "
        "once ticket 2.01 is complete."
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Make the call
# ---------------------------------------------------------------------------
client = Client(ACCOUNT_SID, AUTH_TOKEN)

print(f"[info] Calling {TO_NUMBER} from {FROM_NUMBER} ...")

call = client.calls.create(
    to=TO_NUMBER,
    from_=FROM_NUMBER,
    # Simple TwiML — swap for a URL once you have a webhook:
    # url="http://demo.twilio.com/docs/voice.xml"
    twiml=(
        "<Response>"
        "<Say voice='Polly.Joanna-Generative'>"
        "Hello! This is a test call from your AI voice application. "
        "Everything is working correctly."
        "</Say>"
        "</Response>"
    ),
)

print("[ok] Call initiated!")
print(f"     SID    : {call.sid}")
print(f"     Status : {call.status}")
print(f"     To     : {call.to}")
print(f"     From   : {FROM_NUMBER}")
