"""
Workflow API — submit tasks, stream live SSE logs, approve/reject, get status.
"""
import uuid
import json
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.postgres import get_db
from backend.database.models import Task, WorkflowLog, User
from backend.api.auth import get_current_user, require_manager
from backend.workers.celery_worker import run_workflow_task

router = APIRouter(prefix="/workflow", tags=["Workflow"])
logger = logging.getLogger(__name__)


# ── Schemas ─────────────────────────────────────────────────────────────────

class WorkflowRequest(BaseModel):
    prompt: str


class TaskResponse(BaseModel):
    id: str
    prompt: str
    status: str
    created_at: str
    completed_at: str | None
    result_summary: str | None
    report_path: str | None


class LogResponse(BaseModel):
    id: str
    task_id: str
    agent: str
    status: str
    message: str | None
    output_preview: str | None
    execution_time_ms: float | None
    created_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", status_code=202)
async def submit_workflow(
    req: WorkflowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a new workflow task for multi-agent processing."""
    task = Task(
        user_id=current_user.id,
        prompt=req.prompt,
        status="queued",
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    # Dispatch to Celery
    celery_task = run_workflow_task.delay(
        str(task.id),
        req.prompt,
        str(current_user.id),
    )
    task.celery_task_id = celery_task.id
    await db.flush()

    logger.info(f"Workflow task {task.id} queued (celery: {celery_task.id})")
    return {"task_id": str(task.id), "status": "queued"}


@router.get("/stream/{task_id}")
async def stream_workflow_logs(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Server-Sent Events endpoint — streams live agent log updates in real time.
    Frontend connects via EventSource.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        redis = aioredis.from_url(settings.REDIS_URL)
        channel = f"workflow:{task_id}"
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)

        try:
            # Send heartbeat every 15s to keep connection alive
            heartbeat_counter = 0
            async for message in pubsub.listen():
                if await request.is_disconnected():
                    break

                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode()
                    yield f"data: {data}\n\n"

                    # Check if workflow is terminal
                    try:
                        parsed = json.loads(data)
                        if parsed.get("type") in ("completed", "failed"):
                            break
                    except Exception:
                        pass

                heartbeat_counter += 1
                if heartbeat_counter % 30 == 0:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        finally:
            await pubsub.unsubscribe(channel)
            await redis.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Task).where(
            Task.id == uuid.UUID(task_id),
            Task.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_response(task)


@router.get("/{task_id}/logs", response_model=list[LogResponse])
async def get_task_logs(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkflowLog)
        .where(WorkflowLog.task_id == uuid.UUID(task_id))
        .order_by(WorkflowLog.created_at)
    )
    logs = result.scalars().all()
    return [_log_to_response(log) for log in logs]


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(desc(Task.created_at))
        .limit(50)
    )
    tasks = result.scalars().all()
    return [_task_to_response(t) for t in tasks]


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Human approval checkpoint — allows manager to approve a paused workflow."""
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Task is not awaiting approval")

    # Signal approval via Redis
    redis = aioredis.from_url(settings.REDIS_URL)
    await redis.set(f"approval:{task_id}", "approved", ex=3600)
    await redis.publish(
        f"workflow:{task_id}",
        json.dumps({"type": "approved", "agent": "Human Approval", "message": f"Approved by {current_user.name}"}),
    )
    await redis.aclose()

    task.status = "running"
    return {"message": "Task approved"}


@router.post("/{task_id}/reject")
async def reject_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a paused workflow — terminates it."""
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    redis = aioredis.from_url(settings.REDIS_URL)
    await redis.set(f"approval:{task_id}", "rejected", ex=3600)
    await redis.publish(
        f"workflow:{task_id}",
        json.dumps({"type": "rejected", "agent": "Human Approval", "message": f"Rejected by {current_user.name}"}),
    )
    await redis.aclose()

    task.status = "failed"
    return {"message": "Task rejected"}


@router.get("/pending/approvals")
async def pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Task)
        .where(Task.status == "awaiting_approval")
        .order_by(desc(Task.created_at))
    )
    tasks = result.scalars().all()
    return [_task_to_response(t) for t in tasks]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=str(task.id),
        prompt=task.prompt,
        status=task.status,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        result_summary=task.result_summary,
        report_path=task.report_path,
    )


def _log_to_response(log: WorkflowLog) -> LogResponse:
    return LogResponse(
        id=str(log.id),
        task_id=str(log.task_id),
        agent=log.agent,
        status=log.status,
        message=log.message,
        output_preview=log.output_preview,
        execution_time_ms=log.execution_time_ms,
        created_at=log.created_at.isoformat(),
    )
