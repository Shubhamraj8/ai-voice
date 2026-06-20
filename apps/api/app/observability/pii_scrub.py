"""Shared PII scrubbing rules (ticket 5.18).

Centralizes the redaction logic for the Sentry ``before_send`` hooks (5.16 / 5.17).
A mirror TypeScript implementation lives in ``apps/web/lib/pii-scrub.ts`` with the
same rules; both are exercised against ``packages/shared/pii-fixtures.json``.

Matches are replaced with placeholder tokens ([PHONE], [EMAIL], [AADHAAR], [PAN],
[CARD], [NAME]) so error structure stays debuggable. Allowlisted email domains
(our own staff) are kept so we can debug internal users.
"""

from __future__ import annotations

import re

from app.config import get_settings

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_RE = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
# 13–16 digits with optional single separators — verified with Luhn before redact.
CARD_RE = re.compile(r"\b\d(?:[ -]?\d){12,15}\b")
# +CC / 10+ digit runs (E.164 and spaced Indian formats).
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{8,}\d")


def _luhn_ok(digits: str) -> bool:
    if not (13 <= len(digits) <= 16):
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def default_allowed_domains() -> set[str]:
    raw = get_settings().pii_allowed_email_domains
    return {d.strip().lower() for d in raw.split(",") if d.strip()}


def default_known_names() -> list[str]:
    raw = get_settings().pii_known_names
    return [n.strip() for n in raw.split(",") if n.strip()]


def redact_text(
    text: str,
    *,
    allowed_domains: set[str] | None = None,
    known_names: list[str] | None = None,
) -> str:
    """Replace any PII in ``text`` with placeholder tokens."""

    if not text:
        return text
    allowed = (
        allowed_domains if allowed_domains is not None else default_allowed_domains()
    )
    names = known_names if known_names is not None else default_known_names()

    def _email(match: re.Match[str]) -> str:
        domain = match.group().rsplit("@", 1)[-1].lower()
        return match.group() if domain in allowed else "[EMAIL]"

    def _card(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group())
        return "[CARD]" if _luhn_ok(digits) else match.group()

    out = EMAIL_RE.sub(_email, text)
    out = PAN_RE.sub("[PAN]", out)
    out = CARD_RE.sub(_card, out)
    out = AADHAAR_RE.sub("[AADHAAR]", out)
    out = PHONE_RE.sub("[PHONE]", out)
    for name in names:
        out = re.sub(re.escape(name), "[NAME]", out, flags=re.IGNORECASE)
    return out


def redact_value(
    value: object,
    *,
    allowed_domains: set[str] | None = None,
    known_names: list[str] | None = None,
) -> object:
    """Recursively redact PII in strings nested inside dicts/lists."""

    if isinstance(value, dict):
        return {
            k: redact_value(v, allowed_domains=allowed_domains, known_names=known_names)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            redact_value(v, allowed_domains=allowed_domains, known_names=known_names)
            for v in value
        ]
    if isinstance(value, str):
        return redact_text(
            value, allowed_domains=allowed_domains, known_names=known_names
        )
    return value
