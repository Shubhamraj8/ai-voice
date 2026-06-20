"""Supabase Storage client for call recordings (ticket 2.14).

Uses the service-role key (RLS bypass) to upload recordings and to mint
short-lived signed URLs for playback. Object paths are relative to the
recordings bucket, e.g. ``{tenant_id}/{call_id}.mp3``.
"""

from __future__ import annotations

from urllib.parse import quote

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


def _auth_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }


async def _upload_object(
    *,
    bucket: str,
    path: str,
    data: bytes,
    content_type: str,
) -> bool:
    """Upload bytes to ``{bucket}/{path}`` (overwriting); return True on success."""

    settings = get_settings()
    base = settings.supabase_url.rstrip("/")
    object_url = f"{base}/storage/v1/object/{bucket}/{quote(path, safe='/')}"
    headers = {
        **_auth_headers(),
        "Content-Type": content_type,
        "x-upsert": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(object_url, content=data, headers=headers)
            response.raise_for_status()
        logger.info("object_uploaded", bucket=bucket, path=path, bytes=len(data))
        return True
    except Exception as exc:
        logger.error("object_upload_failed", bucket=bucket, path=path, error=str(exc))
        return False


async def upload_recording(
    *,
    path: str,
    data: bytes,
    content_type: str = "audio/mpeg",
) -> bool:
    """Upload a call recording to the recordings bucket (ticket 2.14)."""
    return await _upload_object(
        bucket=get_settings().recordings_bucket,
        path=path,
        data=data,
        content_type=content_type,
    )


async def upload_document(
    *,
    path: str,
    data: bytes,
    content_type: str = "application/pdf",
) -> bool:
    """Upload a knowledge document to the knowledge bucket (ticket 4.01)."""
    return await _upload_object(
        bucket=get_settings().knowledge_bucket,
        path=path,
        data=data,
        content_type=content_type,
    )


async def _download_object(*, bucket: str, path: str) -> bytes | None:
    """Download an object's bytes from ``{bucket}/{path}``; None on failure."""

    settings = get_settings()
    base = settings.supabase_url.rstrip("/")
    object_url = f"{base}/storage/v1/object/{bucket}/{quote(path, safe='/')}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(object_url, headers=_auth_headers())
            response.raise_for_status()
        return response.content
    except Exception as exc:
        logger.error("object_download_failed", bucket=bucket, path=path, error=str(exc))
        return None


async def download_document(*, path: str) -> bytes | None:
    """Download a knowledge document from the knowledge bucket (ticket 4.03)."""
    return await _download_object(bucket=get_settings().knowledge_bucket, path=path)


async def _delete_object(*, bucket: str, path: str) -> bool:
    """Delete ``{bucket}/{path}``; True on success (or already gone)."""

    settings = get_settings()
    base = settings.supabase_url.rstrip("/")
    object_url = f"{base}/storage/v1/object/{bucket}/{quote(path, safe='/')}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(object_url, headers=_auth_headers())
            response.raise_for_status()
        logger.info("object_deleted", bucket=bucket, path=path)
        return True
    except Exception as exc:
        logger.error("object_delete_failed", bucket=bucket, path=path, error=str(exc))
        return False


async def delete_document(*, path: str) -> bool:
    """Delete a knowledge document from the knowledge bucket (ticket 4.02)."""
    return await _delete_object(bucket=get_settings().knowledge_bucket, path=path)


async def delete_recording(*, path: str) -> bool:
    """Delete a call recording from the recordings bucket (ticket 5.13)."""
    return await _delete_object(bucket=get_settings().recordings_bucket, path=path)


async def upload_export(*, path: str, data: bytes) -> bool:
    """Upload a DPDP data-export ZIP to the exports bucket (ticket 5.12)."""
    return await _upload_object(
        bucket=get_settings().exports_bucket,
        path=path,
        data=data,
        content_type="application/zip",
    )


async def _create_signed_url(*, bucket: str, path: str, expires_in: int) -> str | None:
    """Return a time-limited signed URL for ``{bucket}/{path}``."""

    settings = get_settings()
    base = settings.supabase_url.rstrip("/")
    sign_url = f"{base}/storage/v1/object/sign/{bucket}/{quote(path, safe='/')}"
    headers = {**_auth_headers(), "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                sign_url, json={"expiresIn": expires_in}, headers=headers
            )
            response.raise_for_status()
            signed = response.json().get("signedURL")
    except Exception as exc:
        logger.error("object_sign_failed", bucket=bucket, path=path, error=str(exc))
        return None

    if not signed:
        return None
    # The API returns a path like ``/object/sign/{bucket}/...?token=...``.
    return f"{base}/storage/v1{signed}"


async def create_signed_url(*, path: str, expires_in: int | None = None) -> str | None:
    """Return a time-limited signed URL for ``recordings/{path}`` playback."""

    settings = get_settings()
    ttl = expires_in if expires_in is not None else settings.recording_signed_url_ttl_s
    return await _create_signed_url(
        bucket=settings.recordings_bucket, path=path, expires_in=ttl
    )


async def create_export_signed_url(
    *, path: str, expires_in: int | None = None
) -> str | None:
    """Return a signed download URL for a DPDP export ZIP (ticket 5.12)."""

    settings = get_settings()
    ttl = expires_in if expires_in is not None else settings.export_signed_url_ttl_s
    return await _create_signed_url(
        bucket=settings.exports_bucket, path=path, expires_in=ttl
    )
