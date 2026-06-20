"""Tests for Sentry backend scrubbing + guards (ticket 5.17). No sentry_sdk."""

import uuid

from app.observability import sentry as sentry_mod
from app.observability.scrub import scrub_event


def test_scrub_masks_phone_numbers():
    event = {
        "extra": {
            "from_number": "+919876543210",
            "note": "please call +91 98765 43210 back",
        }
    }
    out = scrub_event(event)
    assert "9876543210" not in str(out)
    assert out["extra"]["from_number"] == "[PHONE]"


def test_scrub_redacts_sensitive_keys():
    event = {
        "request": {"headers": {"Authorization": "Bearer abc", "X-Api-Key": "k"}},
        "extra": {
            "embedding": [0.1, 0.2, 0.3],
            "pdf_content": "confidential document text",
            "password": "hunter2",
        },
    }
    out = scrub_event(event)
    assert out["request"]["headers"]["Authorization"] == "[Filtered]"
    assert out["request"]["headers"]["X-Api-Key"] == "[Filtered]"
    assert out["extra"]["embedding"] == "[Filtered]"
    assert out["extra"]["pdf_content"] == "[Filtered]"
    assert out["extra"]["password"] == "[Filtered]"


def test_scrub_keeps_safe_fields():
    event = {"level": "error", "extra": {"count": 3, "msg": "boom"}}
    out = scrub_event(event)
    assert out["level"] == "error"
    assert out["extra"] == {"count": 3, "msg": "boom"}


def test_init_sentry_noop_without_dsn():
    sentry_mod.init_sentry()  # no SENTRY_DSN in the test env
    assert sentry_mod._enabled is False


def test_set_request_tags_noop_when_disabled():
    # Must not import sentry_sdk or raise when Sentry isn't initialized.
    sentry_mod.set_request_tags(request_id="r1", tenant_id=uuid.uuid4(), call_id="c1")
