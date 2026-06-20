"""Tests for the shared PII scrub pipeline (ticket 5.18).

Uses the shared fixtures so the backend and the frontend mirror exercise the same
rules. Pure functions — no DB, no sentry_sdk.
"""

import json
import time
from pathlib import Path

from app.observability import pii_scrub
from app.observability.scrub import scrub_event

_FIXTURES = json.loads(
    (
        Path(__file__).resolve().parents[3] / "packages/shared/pii-fixtures.json"
    ).read_text(encoding="utf-8")
)["cases"]


def test_shared_fixtures_redacted():
    for case in _FIXTURES:
        out = pii_scrub.redact_text(case["input"])
        for sub in case["expect_contains"]:
            assert sub in out, f"{case['name']}: expected {sub!r} in {out!r}"
        for sub in case["expect_absent"]:
            assert sub not in out, f"{case['name']}: leaked {sub!r} in {out!r}"


def test_luhn_gating():
    assert pii_scrub._luhn_ok("4111111111111111") is True  # valid Visa test number
    assert pii_scrub._luhn_ok("4111111111111112") is False


def test_allowlisted_domain_kept():
    out = pii_scrub.redact_text(
        "internal a@acme.io vs external b@gmail.com", allowed_domains={"acme.io"}
    )
    assert "a@acme.io" in out
    assert "b@gmail.com" not in out
    assert "[EMAIL]" in out


def test_known_name_redacted():
    out = pii_scrub.redact_text("caller Rahul Kumar asked", known_names=["Rahul Kumar"])
    assert "[NAME]" in out
    assert "Rahul Kumar" not in out


def test_scrub_event_redacts_keys_and_nested_pii():
    event = {
        "request": {"headers": {"Authorization": "Bearer secret"}},
        "extra": {"caller": "+919876543210", "note": "email a@gmail.com"},
    }
    out = scrub_event(event)
    assert out["request"]["headers"]["Authorization"] == "[Filtered]"
    assert out["extra"]["caller"] == "[PHONE]"
    assert "[EMAIL]" in out["extra"]["note"]


def test_scrub_performance_under_budget():
    event = {"extra": {f"f{i}": "call +919876543210 or a@gmail.com" for i in range(50)}}
    start = time.perf_counter()
    scrub_event(event)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.05  # generous; the ~5ms target holds in practice
