from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.database import get_db
from app.models.user import User
from app.api.deps import get_current_user, get_user_subject_ids
from app.services.calendar_service import get_calendar_events

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/events")
def calendar_events(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject_ids = get_user_subject_ids(db, current_user.id)
    return get_calendar_events(db, subject_ids, start, end)
