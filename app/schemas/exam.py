from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.exam import ExamType
from app.models.task import Priority


class ExamBase(BaseModel):
    title: str
    exam_type: ExamType = ExamType.other
    exam_date: datetime
    duration: Optional[int] = 60
    location: Optional[str] = None
    priority: Priority = Priority.HIGH
    notes: Optional[str] = None


class ExamCreate(ExamBase):
    subject_id: int


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    exam_type: Optional[ExamType] = None
    exam_date: Optional[datetime] = None
    duration: Optional[int] = None
    location: Optional[str] = None
    priority: Optional[Priority] = None
    notes: Optional[str] = None


class ExamOut(ExamBase):
    id: int
    subject_id: int
    created_at: datetime

    class Config:
        from_attributes = True
