"""
Celery worker tasks for EnterpriseOps AI.
Handles async document processing and workflow execution.
"""
import asyncio
import json
import logging
import time
from datetime import datetime

import redis as sync_redis
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Celery App ───────────────────────────────────────────────────────────────
celery_app = Celery(
    "enterpriseops",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "backend.workers.celery_worker.process_document_task": {"queue": "documents"},
        "backend.workers.celery_worker.run_workflow_task": {"queue": "workflows"},
    },
)

# Sync SQLAlchemy for Celery workers (asyncpg not needed here)
sync_engine = create_engine(settings.DATABASE_SYNC_URL)
SyncSession = sessionmaker(bind=sync_engine)


# ── Document Processing Task ─────────────────────────────────────────────────

@celery_app.task(name="process_document", bind=True, max_retries=3)
def process_document_task(self, document_id: str, file_path: str):
    """
    Background task: Extract text → chunk → embed → store in Qdrant.
    Updates document embedding_status in PostgreSQL.
    """
    from backend.database.models import Document
    from backend.rag.embeddings import extract_text_from_file, chunk_text, embed_texts
    from backend.database.qdrant import (
        ensure_collection_sync, upsert_vectors_sync
    )

    logger.info(f"[Celery] Processing document {document_id}")

    with SyncSession() as session:
        import uuid
        doc = session.get(Document, uuid.UUID(document_id))
        if not doc:
            logger.error(f"Document {document_id} not found in DB")
            return

        try:
            # Update status
            doc.embedding_status = "processing"
            session.commit()

            # Step 1: Extract text
            text = extract_text_from_file(file_path)
            if not text.strip():
                raise ValueError("No text could be extracted from the document")

            # Step 2: Chunk
            chunks = chunk_text(text, chunk_size=512, overlap=64)
            logger.info(f"[Celery] Extracted {len(chunks)} chunks from {document_id}")

            # Step 3: Embed
            vectors = embed_texts(chunks)

            # Step 4: Build payloads
            payloads = [
                {
                    "document_id": document_id,
                    "user_id": str(doc.user_id),
                    "original_filename": doc.original_filename,
                    "file_type": doc.file_type,
                    "chunk_index": i,
                    "text": chunk,
                }
                for i, chunk in enumerate(chunks)
            ]

            # Step 5: Upsert to Qdrant
            ensure_collection_sync()
            point_ids = upsert_vectors_sync(vectors, payloads)

            # Step 6: Update DB
            doc.embedding_status = "done"
            doc.chunk_count = len(chunks)
            doc.qdrant_ids = point_ids
            session.commit()

            logger.info(f"[Celery] Document {document_id} embedded: {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"[Celery] Document processing failed: {e}", exc_info=True)
            doc.embedding_status = "failed"
            session.commit()
            raise self.retry(exc=e, countdown=60)


# ── Workflow Execution Task ───────────────────────────────────────────────────

@celery_app.task(name="run_workflow", bind=True)
def run_workflow_task(self, task_id: str, prompt: str, user_id: str):
    """
    Background task: Run the full LangGraph multi-agent pipeline.
    Publishes live SSE events via Redis pub/sub.
    Updates task status in PostgreSQL.
    """
    from backend.database.models import Task, WorkflowLog
    from backend.agents.graph import run_pipeline
    import uuid

    logger.info(f"[Celery] Starting workflow {task_id}")
    r = sync_redis.Redis.from_url(settings.REDIS_URL)

    with SyncSession() as session:
        task = session.get(Task, uuid.UUID(task_id))
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.status = "running"
        session.commit()

        # Publish start event
        r.publish(f"workflow:{task_id}", json.dumps({
            "type": "workflow_start",
            "agent": "System",
            "status": "running",
            "message": "Workflow started — initializing agent pipeline...",
            "timestamp": time.time(),
        }))

        try:
            # Run async pipeline in sync Celery context
            final_state = asyncio.run(
                run_pipeline(task_id=task_id, user_id=user_id, prompt=prompt)
            )

            # Save workflow logs per agent message
            _save_workflow_logs(session, task_id, final_state)

            # Update task record
            task.status = "completed" if final_state.get("approval_status") != "rejected" else "failed"
            task.completed_at = datetime.utcnow()
            task.report_path = final_state.get("report_path")
            task.result_summary = final_state.get("analytics_summary", "")
            session.commit()

            # Publish completion event
            r.publish(f"workflow:{task_id}", json.dumps({
                "type": "completed",
                "agent": "System",
                "status": "success",
                "message": f"Workflow completed! {final_state.get('analytics_summary', '')}",
                "timestamp": time.time(),
                "report_path": final_state.get("report_path"),
            }))

            logger.info(f"[Celery] Workflow {task_id} completed")

        except Exception as e:
            logger.error(f"[Celery] Workflow {task_id} failed: {e}", exc_info=True)
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            session.commit()

            r.publish(f"workflow:{task_id}", json.dumps({
                "type": "failed",
                "agent": "System",
                "status": "failed",
                "message": f"Workflow failed: {str(e)}",
                "timestamp": time.time(),
            }))

        finally:
            r.close()


def _save_workflow_logs(session, task_id: str, state: dict):
    """Persist per-agent execution status to workflow_logs table."""
    from backend.database.models import WorkflowLog
    import uuid

    agent_keys = [
        ("Planner", "plan"),
        ("Knowledge", "rag_context"),
        ("SQL", "sql_query"),
        ("Analytics", "analytics_summary"),
        ("Report", "report_path"),
        ("Email", "email_message"),
        ("Slack", "slack_message"),
        ("GitHub", "github_issue_url"),
    ]

    for agent_name, result_key in agent_keys:
        result_value = state.get(result_key)
        status = "success" if result_value else "skipped"
        preview = str(result_value)[:500] if result_value else None

        log = WorkflowLog(
            task_id=uuid.UUID(task_id),
            agent=agent_name,
            status=status,
            message=f"{agent_name} completed",
            output_preview=preview,
        )
        session.add(log)

    session.commit()
