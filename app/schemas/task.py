from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.task import TaskType, Priority, TaskStatus


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: TaskType = TaskType.other
    priority: Priority = Priority.MEDIUM
    due_date: datetime
    estimated_hours: Optional[float] = 1.0
    recurrence_rule: Optional[str] = None  # DAILY | WEEKLY | MONTHLY | None
    recurrence_end_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    subject_id: int
    parent_task_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TaskType] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    subject_id: Optional[int] = None


class TaskOut(TaskBase):
    id: int
    subject_id: int
    parent_task_id: Optional[int] = None
    status: TaskStatus
    priority_score: float
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskWithSubtasks(TaskOut):
    subtasks: List["TaskOut"] = []

    class Config:
        from_attributes = True
