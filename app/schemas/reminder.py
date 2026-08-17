from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.reminder import NotificationType


class ReminderBase(BaseModel):
    reminder_time: datetime
    notification_type: NotificationType = NotificationType.in_app
    message: Optional[str] = None


class ReminderCreate(ReminderBase):
    task_id: Optional[int] = None
    exam_id: Optional[int] = None


class ReminderOut(ReminderBase):
    id: int
    user_id: int
    task_id: Optional[int] = None
    exam_id: Optional[int] = None
    is_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True
