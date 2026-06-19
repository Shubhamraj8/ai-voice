"""DPDP data export (ticket 5.12).

Collects everything we hold for one tenant — tenant row, members, agents, calls
+ messages, knowledge docs (metadata + the original PDFs), billing events, and
the tenant-scoped audit log — into a ZIP (one JSON per table + the PDF files),
uploads it to ``exports/{tenant_id}/{export_id}.zip``, and emails the requester
a 7-day signed download link. Every query is scoped to the tenant, so no other
tenant's data can leak.

Runs as a fire-and-forget background task scheduled from the request handler.
"""

from __future__ import annotations

import asyncio
import io
import json
import zipfile
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import structlog

from app.db.pool import get_pool
from app.services.audit import log_system_action
from app.services.email import send_email
from app.services.storage import (
    create_export_signed_url,
    download_document,
    upload_export,
)

logger = structlog.get_logger(__name__)

# Keep references to running tasks so they are not garbage-collected mid-flight.
_background_tasks: set[asyncio.Task] = set()

# table name -> SQL (each filtered to the one tenant via $1)
_TABLE_QUERIES: dict[str, str] = {
    "users": "SELECT user_id, role, created_at FROM tenant_users WHERE tenant_id = $1",
    "agents": "SELECT * FROM agents WHERE tenant_id = $1",
    "calls": "SELECT * FROM calls WHERE tenant_id = $1 ORDER BY started_at",
    "call_messages": (
        "SELECT * FROM call_messages WHERE tenant_id = $1 ORDER BY created_at"
    ),
    "knowledge_documents": "SELECT * FROM knowledge_documents WHERE tenant_id = $1",
    "billing_events": (
        "SELECT * FROM billing_events WHERE tenant_id = $1 ORDER BY created_at"
    ),
    "audit_log": "SELECT * FROM audit_log WHERE tenant_id = $1 ORDER BY created_at",
}


def _json_default(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def _build_zip(tables: dict[str, list[dict]], pdfs: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, rows in tables.items():
            archive.writestr(
                f"{name}.json", json.dumps(rows, default=_json_default, indent=2)
            )
        for filename, content in pdfs:
            archive.writestr(f"documents/{filename}", content)
    return buffer.getvalue()


async def _collect(
    tenant_id: UUID,
) -> tuple[dict[str, list[dict]], list[tuple[str, bytes]]]:
    pool = get_pool()
    async with pool.acquire() as conn:
        tenant = await conn.fetchrow("SELECT * FROM tenants WHERE id = $1", tenant_id)
        tables: dict[str, list[dict]] = {
            "tenant": [dict(tenant)] if tenant else [],
        }
        for name, query in _TABLE_QUERIES.items():
            rows = await conn.fetch(query, tenant_id)
            tables[name] = [dict(row) for row in rows]

    # Fetch the original PDFs for the knowledge documents.
    pdfs: list[tuple[str, bytes]] = []
    for doc in tables.get("knowledge_documents", []):
        path = doc.get("storage_path")
        if not path:
            continue
        content = await download_document(path=path)
        if content is None:
            logger.warning("dpdp_export_pdf_missing", document_id=str(doc.get("id")))
            continue
        pdfs.append((f"{doc.get('id')}_{doc.get('filename')}", content))

    return tables, pdfs


async def run_dpdp_export(
    tenant_id: UUID, export_id: UUID, *, recipient_email: str | None = None
) -> None:
    """Build, upload, and email a tenant's data export. Best-effort + audited."""

    try:
        tables, pdfs = await _collect(tenant_id)
        zip_bytes = _build_zip(tables, pdfs)
        path = f"{tenant_id}/{export_id}.zip"

        if not await upload_export(path=path, data=zip_bytes):
            raise RuntimeError("export upload failed")

        await log_system_action(
            "dpdp.export.completed",
            tenant_id=tenant_id,
            target_type="export",
            target_id=export_id,
            payload={"bytes": len(zip_bytes), "documents": len(pdfs)},
        )

        url = await create_export_signed_url(path=path)
        if recipient_email and url:
            await send_email(
                to=recipient_email,
                subject="Your ZERQO data export is ready",
                html=(
                    "<h2>Your data export is ready</h2>"
                    "<p>Your export is available for the next 7 days:</p>"
                    f'<p><a href="{url}">Download your data (ZIP)</a></p>'
                    "<p>The link expires after 7 days for your security.</p>"
                ),
            )
            await log_system_action(
                "dpdp.export.emailed",
                tenant_id=tenant_id,
                target_type="export",
                target_id=export_id,
                payload={"to": recipient_email},
            )
        logger.info(
            "dpdp_export_done",
            tenant_id=str(tenant_id),
            export_id=str(export_id),
            bytes=len(zip_bytes),
        )
    except Exception as exc:
        logger.error(
            "dpdp_export_failed",
            tenant_id=str(tenant_id),
            export_id=str(export_id),
            error=str(exc),
        )


def schedule_export(
    tenant_id: UUID, export_id: UUID, *, recipient_email: str | None = None
) -> None:
    """Run an export in the background, keeping a reference until it completes."""

    task = asyncio.create_task(
        run_dpdp_export(tenant_id, export_id, recipient_email=recipient_email)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
