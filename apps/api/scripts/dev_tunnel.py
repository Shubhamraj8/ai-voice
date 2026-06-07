"""
dev_tunnel.py — Start an ngrok tunnel to the local FastAPI instance (ticket 2.03).

Usage:
    python apps/api/scripts/dev_tunnel.py

What it does:
    1. Starts ngrok HTTP tunnel → localhost:8000
    2. Fetches the public URL from the ngrok local API
    3. Prints the webhook URL to paste into Twilio Console
    4. Optionally updates the Twilio number's Voice URL automatically
       (set TWILIO_AUTO_UPDATE_WEBHOOK=true in .env to enable)

Prerequisites:
    pip install twilio requests
    ngrok must be installed and on PATH  (https://ngrok.com/download)
    Optional: set NGROK_AUTHTOKEN in .env for a stable subdomain
"""

import os
import subprocess
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Load .env from repo root
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.abspath(os.path.join(_here, "..", "..", ".."))
    load_dotenv(os.path.join(_root, ".env"))
    print("[info] Loaded .env")
except ImportError:
    pass

NGROK_LOCAL_API = "http://127.0.0.1:4040/api/tunnels"
FASTAPI_PORT = int(os.environ.get("FASTAPI_PORT", "8000"))

# Twilio (optional auto-update)
ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
AUTO_UPDATE = os.environ.get("TWILIO_AUTO_UPDATE_WEBHOOK", "false").lower() == "true"

# ngrok
NGROK_AUTHTOKEN = os.environ.get("NGROK_AUTHTOKEN", "")
NGROK_SUBDOMAIN = os.environ.get("NGROK_SUBDOMAIN", "")  # paid plan only


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_tunnel_url(retries: int = 15, delay: float = 1.0) -> str:
    """Poll the ngrok local API until a tunnel URL is available."""
    for attempt in range(retries):
        try:
            resp = requests.get(NGROK_LOCAL_API, timeout=3)
            tunnels = resp.json().get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    return t["public_url"]
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(delay)
        print(f"[info] Waiting for ngrok tunnel... ({attempt + 1}/{retries})")
    raise RuntimeError("ngrok tunnel did not start in time.")


def update_twilio_webhook(public_url: str) -> None:
    """Update the Twilio number's Voice URL to point at the ngrok tunnel."""
    if not all([ACCOUNT_SID, AUTH_TOKEN, PHONE_NUMBER]):
        print(
            "[warn] Skipping Twilio auto-update — "
            "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_PHONE_NUMBER not set."
        )
        return

    try:
        from twilio.rest import Client  # type: ignore[import]
    except ImportError:
        print("[warn] twilio SDK not installed — skipping auto-update.")
        return

    webhook_url = f"{public_url}/webhooks/twilio/voice"
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    numbers = client.incoming_phone_numbers.list(phone_number=PHONE_NUMBER)
    if not numbers:
        print(f"[warn] Phone number {PHONE_NUMBER} not found in Twilio account.")
        return

    numbers[0].update(voice_url=webhook_url, voice_method="POST")
    print(f"[twilio] Voice URL updated -> {webhook_url}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # Build ngrok command
    ngrok_bin = "ngrok"
    if sys.platform == "win32":
        import shutil

        if not shutil.which(ngrok_bin):
            winget_path = os.path.expandvars(
                r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
            )
            if os.path.exists(winget_path):
                ngrok_bin = winget_path

    cmd = [ngrok_bin, "http", str(FASTAPI_PORT), "--log=stdout"]
    if NGROK_AUTHTOKEN:
        cmd += ["--authtoken", NGROK_AUTHTOKEN]
    if NGROK_SUBDOMAIN:
        cmd += ["--subdomain", NGROK_SUBDOMAIN]

    print(f"[info] Starting ngrok tunnel -> localhost:{FASTAPI_PORT}")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        public_url = get_tunnel_url()
    except RuntimeError as exc:
        proc.terminate()
        print(f"[error] {exc}")
        sys.exit(1)

    webhook_url = f"{public_url}/webhooks/twilio/voice"

    print()
    print("=" * 60)
    print(f"  ngrok tunnel:   {public_url}")
    print(f"  Twilio webhook: {webhook_url}")
    print()
    print("  Paste the webhook URL into Twilio Console:")
    print("  Phone Numbers -> Manage -> Active Numbers -> Voice URL")
    print("=" * 60)
    print()

    if AUTO_UPDATE:
        update_twilio_webhook(public_url)
    else:
        print(
            "[info] Set TWILIO_AUTO_UPDATE_WEBHOOK=true in .env to update "
            "Twilio automatically on each tunnel start."
        )

    print("[info] Tunnel running. Press Ctrl+C to stop.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n[info] Shutting down ngrok.")
        proc.terminate()


if __name__ == "__main__":
    main()
