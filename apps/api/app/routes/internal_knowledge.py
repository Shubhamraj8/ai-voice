from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from app.db.pool import get_pool
from app.middleware.auth import InternalUserContext, require_internal_user
from app.models.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeDocumentDetail,
)
from app.services.audit import log_internal_action
from app.services.ingestion import process_document
from app.services.knowledge import (
    compute_sha256,
    get_document_detail,
    list_document_chunks,
    list_documents,
    mark_for_reprocess,
    soft_delete_document,
    store_document,
    validate_pdf,
)
from app.services.storage import delete_document

router = APIRouter(
    prefix="/internal/tenants/{tenant_id}/knowledge", tags=["internal-knowledge"]
)


def _object_path(storage_path: str) -> str:
    """Strip the ``{bucket}/`` prefix from a stored path to get the object key."""
    return storage_path.split("/", 1)[1] if "/" in storage_path else storage_path


@router.post("", response_model=KnowledgeDocument, status_code=201)
async def upload_knowledge_document(
    tenant_id: UUID,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pool=Depends(get_pool),
) -> KnowledgeDocument:
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

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.knowledge.upload",
        tenant_id=tenant_id,
        target_type="knowledge_document",
        target_id=document.id,
        payload={"filename": document.filename, "bytes": document.bytes},
    )

    # Ingest in the background so the upload returns immediately; progress is
    # reflected on the document's status field (ticket 4.03).
    background_tasks.add_task(process_document, document.id)
    return document


@router.get("", response_model=list[KnowledgeDocument])
async def list_knowledge_documents(
    tenant_id: UUID,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> list[KnowledgeDocument]:
    async with pool.acquire() as conn:
        return await list_documents(conn, tenant_id=tenant_id)


@router.get("/{document_id}", response_model=KnowledgeDocumentDetail)
async def get_knowledge_document(
    tenant_id: UUID,
    document_id: UUID,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> KnowledgeDocumentDetail:
    async with pool.acquire() as conn:
        return await get_document_detail(
            conn, tenant_id=tenant_id, document_id=document_id
        )


@router.get("/{document_id}/chunks", response_model=list[KnowledgeChunk])
async def get_knowledge_document_chunks(
    tenant_id: UUID,
    document_id: UUID,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    limit: int = 3,
    pool=Depends(get_pool),
) -> list[KnowledgeChunk]:
    async with pool.acquire() as conn:
        return await list_document_chunks(
            conn, tenant_id=tenant_id, document_id=document_id, limit=min(limit, 20)
        )


@router.post("/{document_id}/reprocess", status_code=202)
async def reprocess_knowledge_document(
    tenant_id: UUID,
    document_id: UUID,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    background_tasks: BackgroundTasks,
    pool=Depends(get_pool),
) -> dict[str, str]:
    async with pool.acquire() as conn:
        await mark_for_reprocess(conn, tenant_id=tenant_id, document_id=document_id)

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.knowledge.reprocess",
        tenant_id=tenant_id,
        target_type="knowledge_document",
        target_id=document_id,
    )
    background_tasks.add_task(process_document, document_id)
    return {"status": "pending"}


@router.delete("/{document_id}", status_code=204)
async def delete_knowledge_document(
    tenant_id: UUID,
    document_id: UUID,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> None:
    async with pool.acquire() as conn:
        storage_path = await soft_delete_document(
            conn, tenant_id=tenant_id, document_id=document_id
        )

    # The row + embeddings are gone transactionally; the file is best-effort.
    await delete_document(path=_object_path(storage_path))

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.knowledge.delete",
        tenant_id=tenant_id,
        target_type="knowledge_document",
        target_id=document_id,
    )
