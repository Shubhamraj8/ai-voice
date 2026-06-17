"""Tests for agent tool-whitelist validation (ticket 4.11). No pipecat import."""

import pytest
from app.services.agent_internal import validate_tools
from fastapi import HTTPException


def test_empty_or_none_is_allowed():
    validate_tools(None)
    validate_tools([])  # no raise


def test_known_tools_pass():
    # Registered by app.tools.builtin (4.08–4.10).
    validate_tools(["transferToHuman", "sendSms", "escalateToOwner"])


def test_unknown_tool_rejected():
    with pytest.raises(HTTPException) as exc:
        validate_tools(["transferToHuman", "doesNotExist"])

    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "invalid_tools"
    assert "doesNotExist" in exc.value.detail["message"]
    assert "transferToHuman" in exc.value.detail["allowed"]
