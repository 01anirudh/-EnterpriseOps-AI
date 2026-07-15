"""
SQLAlchemy async models for EnterpriseOps AI.
Tables: users, documents, tasks, workflow_logs
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, Integer,
    ForeignKey, Boolean, Float, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # user | manager | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="user", lazy="selectin")
    documents = relationship("Document", back_populates="user", lazy="selectin")

    def __repr__(self):
        return f"<User {self.email}>"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(50))  # pdf | docx | xlsx | csv | txt
    file_size = Column(Integer)  # bytes
    embedding_status = Column(String(50), default="pending")  # pending | processing | done | failed
    chunk_count = Column(Integer, default=0)
    qdrant_ids = Column(JSON, default=list)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.original_filename}>"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    status = Column(String(50), default="queued")  # queued | running | awaiting_approval | completed | failed
    celery_task_id = Column(String(255))
    result_summary = Column(Text)
    report_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="tasks")
    logs = relationship("WorkflowLog", back_populates="task", lazy="selectin", order_by="WorkflowLog.created_at")

    def __repr__(self):
        return f"<Task {self.id} [{self.status}]>"


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    agent = Column(String(100), nullable=False)
    status = Column(String(50), default="running")  # running | success | failed | skipped
    message = Column(Text)
    output_preview = Column(Text)
    execution_time_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="logs")

    def __repr__(self):
        return f"<WorkflowLog {self.agent} [{self.status}]>"
