from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.post("", response_model=ReminderOut, status_code=201)
def create_reminder(payload: ReminderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reminder = Reminder(user_id=current_user.id, **payload.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("", response_model=List[ReminderOut])
def list_reminders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Reminder).filter(Reminder.user_id == current_user.id).order_by(Reminder.reminder_time.asc()).all()


@router.get("/pending", response_model=List[ReminderOut])
def pending_reminders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fallback endpoint for the frontend to poll on load, in case a
    WebSocket push was missed while the tab was closed."""
    return (
        db.query(Reminder)
        .filter(Reminder.user_id == current_user.id, Reminder.is_sent == False)  # noqa: E712
        .order_by(Reminder.reminder_time.asc())
        .all()
    )


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()
    return None
