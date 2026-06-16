from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile

from app.db.pool import get_pool
from app.middleware.auth import InternalUserContext, require_internal_user
from app.models.knowledge import KnowledgeDocument
from app.services.audit import log_internal_action
from app.services.knowledge import compute_sha256, store_document, validate_pdf

router = APIRouter(
    prefix="/internal/tenants/{tenant_id}/knowledge", tags=["internal-knowledge"]
)


@router.post("", response_model=KnowledgeDocument, status_code=201)
async def upload_knowledge_document(
    tenant_id: UUID,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
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
    return document
