"""Sentry backend init + request tagging (ticket 5.17).

``sentry_sdk`` is imported lazily inside ``init_sentry`` so the app has no hard
dependency on it when the DSN is unset (local/dev) — the same guard pattern as
Redis/Resend. Tagging helpers no-op until Sentry is initialized.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from app.config import get_settings
from app.observability.scrub import scrub_event

logger = structlog.get_logger(__name__)

_enabled = False


def init_sentry() -> None:
    """Initialize Sentry if a DSN is configured; otherwise a no-op."""

    global _enabled
    settings = get_settings()
    if not settings.sentry_dsn:
        logger.info("sentry_disabled_no_dsn")
        return

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        # 100% of errors, 5% of performance traces (ticket 5.17).
        sample_rate=1.0,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
        release=settings.render_git_commit or None,
        environment=settings.sentry_environment or None,
        before_send=scrub_event,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    _enabled = True
    logger.info("sentry_initialized")


def set_request_tags(
    *,
    request_id: str | None = None,
    tenant_id: UUID | str | None = None,
    call_id: UUID | str | None = None,
) -> None:
    """Tag the current Sentry scope. No-op when Sentry isn't initialized."""

    if not _enabled:
        return

    import sentry_sdk

    if request_id:
        sentry_sdk.set_tag("request_id", request_id)
    if tenant_id:
        sentry_sdk.set_tag("tenant_id", str(tenant_id))
    if call_id:
        sentry_sdk.set_tag("call_id", str(call_id))
