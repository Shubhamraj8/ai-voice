"""Tenant-facing knowledge base management (client portal).

Mirrors the internal knowledge routes but scopes everything to the caller's own
tenant (from the auth context, never a path param), reusing the same ingestion
pipeline and service layer.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from app.db.pool import get_pool
from app.middleware.auth import (
    TenantContext,
    User,
    get_current_tenant,
    get_current_user,
)
from app.models.knowledge import KnowledgeDocument
from app.services.audit import log_tenant_action
from app.services.ingestion import process_document
from app.services.knowledge import (
    compute_sha256,
    list_documents,
    soft_delete_document,
    store_document,
    validate_pdf,
)
from app.services.storage import delete_document

router = APIRouter(prefix="/portal/knowledge", tags=["portal-knowledge"])


def _object_path(storage_path: str) -> str:
    return storage_path.split("/", 1)[1] if "/" in storage_path else storage_path


@router.get("", response_model=list[KnowledgeDocument])
async def list_portal_knowledge(
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
    pool=Depends(get_pool),
) -> list[KnowledgeDocument]:
    async with pool.acquire() as conn:
        return await list_documents(conn, tenant_id=tenant_context.tenant.id)


@router.post("", response_model=KnowledgeDocument, status_code=201)
async def upload_portal_knowledge(
    user: Annotated[User, Depends(get_current_user)],
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pool=Depends(get_pool),
) -> KnowledgeDocument:
    tenant_id = tenant_context.tenant.id
    data = await file.read()
    validate_pdf(data=data, content_type=file.content_type)
    sha256 = compute_sha256(data)

    async with pool.acquire() as conn:
        document = await store_document(
            conn,
            tenant_id=tenant_id,
            filename=file.filename or "document.pdf",
            data=data,
            sha256=sha256,
        )

    await log_tenant_action(
        user.id,
        "portal.knowledge.upload",
        tenant_id=tenant_id,
        target_type="knowledge_document",
        target_id=document.id,
        payload={"filename": document.filename, "bytes": document.bytes},
    )
    # Ingest in the background; progress shows on the document's status field.
    background_tasks.add_task(process_document, document.id)
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_portal_knowledge(
    document_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
    pool=Depends(get_pool),
) -> None:
    tenant_id = tenant_context.tenant.id
    async with pool.acquire() as conn:
        storage_path = await soft_delete_document(
            conn, tenant_id=tenant_id, document_id=document_id
        )

    await delete_document(path=_object_path(storage_path))

    await log_tenant_action(
        user.id,
        "portal.knowledge.delete",
        tenant_id=tenant_id,
        target_type="knowledge_document",
        target_id=document_id,
    )
