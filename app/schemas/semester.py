from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class SemesterBase(BaseModel):
    name: str
    start_date: date
    end_date: date


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class SemesterOut(SemesterBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
