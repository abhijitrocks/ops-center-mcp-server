from sqlmodel import SQLModel, Field
from typing import Optional, Dict
from datetime import datetime

class Tenant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int
    tag_name: str
    tag_info: Optional[Dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TaskQueueMapping(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int
    workbench_id: int
    task_id: int
    queue_id: int
    potential_queue_id: Optional[int] = None
    criteria: Optional[Dict] = None
    attributes: Optional[Dict] = None

class UserTaskInfo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent: str
    task_id: int
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    process_instance_id: Optional[int] = None
    workbench_id: Optional[int] = None

class HistoryTaskInfo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict] = None
