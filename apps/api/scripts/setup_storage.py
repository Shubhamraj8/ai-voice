"""
setup_storage.py — create the private 'recordings' Storage bucket (ticket 2.14)

Idempotent: safe to run repeatedly. Creates the bucket via the Supabase
Storage API using the service-role key. Migration 011 also registers the bucket
+ policies in SQL; this script is the supported API path and a quick verify.

Usage (from the repo root, with .env populated):
    python apps/api/scripts/setup_storage.py
"""

import os
import sys

try:
    from dotenv import load_dotenv

    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.abspath(os.path.join(_here, "..", "..", ".."))
    _env_path = os.path.join(_root, ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
        print(f"[info] Loaded env from {_env_path}")
except ImportError:
    pass

import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = os.environ.get("RECORDINGS_BUCKET", "recordings")

missing = [
    k
    for k, v in {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_ROLE_KEY": SERVICE_ROLE_KEY,
    }.items()
    if not v
]
if missing:
    print(f"[error] Missing env vars: {', '.join(missing)}")
    sys.exit(1)

base = SUPABASE_URL.rstrip("/")
headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

print(f"[info] Ensuring private bucket '{BUCKET}' exists ...")
resp = httpx.post(
    f"{base}/storage/v1/bucket",
    headers=headers,
    json={"id": BUCKET, "name": BUCKET, "public": False},
    timeout=30.0,
)

if resp.status_code in (200, 201):
    print(f"[ok] Bucket '{BUCKET}' created.")
elif resp.status_code == 409 or "already exists" in resp.text.lower():
    print(f"[ok] Bucket '{BUCKET}' already exists — nothing to do.")
else:
    print(f"[error] Unexpected response {resp.status_code}: {resp.text}")
    sys.exit(1)

# Verify it is private.
verify = httpx.get(f"{base}/storage/v1/bucket/{BUCKET}", headers=headers, timeout=30.0)
if verify.status_code == 200:
    is_public = verify.json().get("public")
    print(f"[info] Bucket public={is_public} (expected False).")
else:
    print(f"[warn] Could not verify bucket: {verify.status_code}")
