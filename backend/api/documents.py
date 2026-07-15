"""
Document upload and management API.
Handles file ingestion, text extraction, chunking, and RAG embedding.
"""
import os
import uuid
import logging
from pathlib import Path
from typing import List

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.postgres import get_db
from backend.database.models import Document, User
from backend.api.auth import get_current_user
from backend.workers.celery_worker import process_document_task

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/csv": "csv",
    "text/plain": "txt",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# ── Schemas ─────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    embedding_status: str
    chunk_count: int
    uploaded_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES and not file.filename.endswith((".pdf", ".docx", ".xlsx", ".csv", ".txt")):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

    # Detect file type from extension if content-type is generic
    ext = Path(file.filename).suffix.lower().lstrip(".")
    file_type = ALLOWED_TYPES.get(content_type, ext)

    # Ensure upload directory exists
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    # Generate unique stored filename
    stored_name = f"{uuid.uuid4()}.{file_type}"
    file_path = upload_path / stored_name

    # Save file to disk
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create DB record
    doc = Document(
        user_id=current_user.id,
        filename=stored_name,
        original_filename=file.filename,
        file_type=file_type,
        file_size=len(content),
        embedding_status="pending",
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # Trigger Celery task for embedding
    process_document_task.delay(str(doc.id), str(file_path))

    logger.info(f"Document {doc.id} uploaded by user {current_user.id}")
    return {
        "document_id": str(doc.id),
        "filename": file.filename,
        "status": "pending",
        "message": "Document uploaded. Processing in background.",
    }


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    )
    docs = result.scalars().all()
    return [
        DocumentResponse(
            id=str(d.id),
            filename=d.filename,
            original_filename=d.original_filename,
            file_type=d.file_type or "",
            file_size=d.file_size or 0,
            embedding_status=d.embedding_status,
            chunk_count=d.chunk_count or 0,
            uploaded_at=d.uploaded_at.isoformat(),
        )
        for d in docs
    ]


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(
            Document.id == uuid.UUID(document_id),
            Document.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    file_path = Path(settings.UPLOAD_DIR) / doc.filename
    if file_path.exists():
        file_path.unlink()

    await db.delete(doc)
    return None
