from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, JSON


class Tenant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int
    tag_name: str
    tag_info: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskQueueMapping(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int
    workbench_id: int
    task_id: int
    queue_id: int
    potential_queue_id: Optional[int] = None
    criteria: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    attributes: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )


class UserTaskInfo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent: str
    task_id: int
    status: str  # e.g., 'completed', 'pending'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    process_instance_id: Optional[int] = None
    workbench_id: Optional[int] = None


class HistoryTaskInfo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int
    event_type: str  # e.g., 'create', 'complete', 'update'
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
