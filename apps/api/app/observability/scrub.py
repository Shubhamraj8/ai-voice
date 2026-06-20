"""Sentry ``before_send`` PII scrubber (ticket 5.17).

Pure dict transform (no sentry_sdk import) so it's trivially testable. Walks the
whole event and:

- redacts values under sensitive keys (auth tokens, cookies, api keys, raw
  embeddings, PDF/document content),
- masks phone numbers anywhere in string values (caller numbers must never leak).

The shared/extended PII pipeline is centralized in 5.18.
"""

from __future__ import annotations

import re

_SENSITIVE_KEY = re.compile(
    r"(token|secret|password|api[_-]?key|apikey|authorization|cookie|"
    r"embedding|embeddings|pdf_content|document_content|content_b64)",
    re.IGNORECASE,
)
_REDACTED = "[Filtered]"

# A run of 10+ digits (with spaces/dashes/parens/leading +) — phone-number-ish.
_PHONE = re.compile(r"\+?\d[\d\s\-()]{8,}\d")


def _mask_phone(match: re.Match[str]) -> str:
    raw = match.group()
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 10:
        return raw
    return f"XXXXX X{digits[-4:]}"


def _scrub(value: object) -> object:
    if isinstance(value, dict):
        out: dict = {}
        for key, val in value.items():
            if isinstance(key, str) and _SENSITIVE_KEY.search(key):
                out[key] = _REDACTED
            else:
                out[key] = _scrub(val)
        return out
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _PHONE.sub(_mask_phone, value)
    return value


def scrub_event(event: dict, _hint: dict | None = None) -> dict:
    """Sentry ``before_send`` hook: scrub PII from the event in place-ish."""
    return _scrub(event)  # type: ignore[return-value]
