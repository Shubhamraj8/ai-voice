"""Sentry ``before_send`` scrubber (tickets 5.17, 5.18).

Walks the whole event and (a) redacts values under sensitive keys (auth tokens,
cookies, api keys, raw embeddings, PDF/document content), and (b) runs every
string through the shared PII pipeline (``pii_scrub``) so phones, emails,
Aadhaar/PAN ids, and cards never leak. Pure dict transform — no sentry_sdk import.
"""

from __future__ import annotations

import re

from app.observability import pii_scrub

_SENSITIVE_KEY = re.compile(
    r"(token|secret|password|api[_-]?key|apikey|authorization|cookie|"
    r"embedding|embeddings|pdf_content|document_content|content_b64)",
    re.IGNORECASE,
)
_REDACTED = "[Filtered]"


def _scrub(value: object, allowed: set[str], names: list[str]) -> object:
    if isinstance(value, dict):
        out: dict = {}
        for key, val in value.items():
            if isinstance(key, str) and _SENSITIVE_KEY.search(key):
                out[key] = _REDACTED
            else:
                out[key] = _scrub(val, allowed, names)
        return out
    if isinstance(value, (list, tuple)):
        return [_scrub(item, allowed, names) for item in value]
    if isinstance(value, str):
        return pii_scrub.redact_text(value, allowed_domains=allowed, known_names=names)
    return value


def scrub_event(event: dict, _hint: dict | None = None) -> dict:
    """Sentry ``before_send`` hook: strip sensitive keys + redact PII everywhere."""
    allowed = pii_scrub.default_allowed_domains()
    names = pii_scrub.default_known_names()
    return _scrub(event, allowed, names)  # type: ignore[return-value]
