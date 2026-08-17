from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.study_session import SessionStatus


class StudySessionBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    is_pomodoro: Optional[bool] = False


class StudySessionCreate(StudySessionBase):
    subject_id: int


class StudySessionUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[SessionStatus] = None
    notes: Optional[str] = None
    pomodoro_count: Optional[int] = None


class StudySessionOut(StudySessionBase):
    id: int
    subject_id: int
    duration: int
    status: SessionStatus
    pomodoro_count: int
    created_at: datetime

    class Config:
        from_attributes = True
