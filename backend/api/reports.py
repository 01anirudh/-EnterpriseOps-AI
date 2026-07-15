"""
Reports API — retrieve generated executive reports.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.postgres import get_db
from backend.database.models import Task, User
from backend.api.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{task_id}")
async def get_report(
    task_id: str,
    format: str = "markdown",  # markdown | html | pdf
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a generated report by task ID."""
    result = await db.execute(
        select(Task).where(
            Task.id == uuid.UUID(task_id),
            Task.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.report_path:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    report_path = Path(task.report_path)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    if format == "pdf":
        pdf_path = report_path.with_suffix(".pdf")
        if pdf_path.exists():
            return FileResponse(
                path=str(pdf_path),
                media_type="application/pdf",
                filename=f"report_{task_id}.pdf",
            )
        raise HTTPException(status_code=404, detail="PDF version not available")

    if format == "html":
        import markdown as md
        content = report_path.read_text(encoding="utf-8")
        html = md.markdown(content, extensions=["tables", "fenced_code"])
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=f"<html><body>{html}</body></html>")

    # Default: return raw Markdown
    content = report_path.read_text(encoding="utf-8")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=content, media_type="text/markdown")


@router.get("")
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all completed tasks with reports."""
    result = await db.execute(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.report_path.is_not(None),
        ).order_by(Task.completed_at.desc())
    )
    tasks = result.scalars().all()
    return [
        {
            "task_id": str(t.id),
            "prompt": t.prompt[:100],
            "status": t.status,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "result_summary": t.result_summary,
        }
        for t in tasks
    ]
