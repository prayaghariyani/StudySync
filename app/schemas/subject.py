from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SubjectBase(BaseModel):
    name: str
    code: Optional[str] = None
    teacher: Optional[str] = None
    credits: Optional[int] = 0
    color: Optional[str] = "#6366f1"


class SubjectCreate(SubjectBase):
    semester_id: int


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    teacher: Optional[str] = None
    credits: Optional[int] = None
    color: Optional[str] = None


class SubjectOut(SubjectBase):
    id: int
    semester_id: int
    created_at: datetime

    class Config:
        from_attributes = True
