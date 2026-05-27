"""Fail if RLS test *calls* exceed 10s (ticket 1.05; excludes seed/teardown)."""

from __future__ import annotations

import pytest

_CALL_SECONDS = 0.0
_CALL_COUNT = 0


@pytest.hookimpl(trylast=True)
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    global _CALL_SECONDS, _CALL_COUNT
    if report.when == "call" and report.duration is not None:
        _CALL_SECONDS += report.duration
        _CALL_COUNT += 1


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if _CALL_COUNT == 0:
        return
    if _CALL_SECONDS >= 10 and exitstatus == 0:
        session.exitstatus = 1
        print(f"\nRLS test calls exceeded 10s limit ({_CALL_SECONDS:.2f}s)")
