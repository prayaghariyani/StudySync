"""Reminder service: creating default reminders and finding due ones."""
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.models.reminder import Reminder, NotificationType
from app.models.task import Task
from app.models.exam import Exam


def create_default_reminders_for_task(db: Session, user_id: int, task: Task) -> List[Reminder]:
    """Create sensible default reminders: 1 day before and 1 hour before due."""
    offsets = [timedelta(days=1), timedelta(hours=1)]
    reminders = []
    for offset in offsets:
        remind_at = task.due_date - offset
        if remind_at > datetime.utcnow():
            r = Reminder(
                user_id=user_id,
                task_id=task.id,
                reminder_time=remind_at,
                notification_type=NotificationType.in_app,
                message=f"'{task.title}' is due soon",
            )
            db.add(r)
            reminders.append(r)
    if reminders:
        db.commit()
    return reminders


def create_default_reminders_for_exam(db: Session, user_id: int, exam: Exam) -> List[Reminder]:
    offsets = [timedelta(days=2), timedelta(hours=3)]
    reminders = []
    for offset in offsets:
        remind_at = exam.exam_date - offset
        if remind_at > datetime.utcnow():
            r = Reminder(
                user_id=user_id,
                exam_id=exam.id,
                reminder_time=remind_at,
                notification_type=NotificationType.in_app,
                message=f"Exam '{exam.title}' is coming up",
            )
            db.add(r)
            reminders.append(r)
    if reminders:
        db.commit()
    return reminders


def get_due_reminders(db: Session) -> List[Reminder]:
    """Reminders whose time has arrived and haven't been sent yet — used by the scheduler."""
    now = datetime.utcnow()
    return (
        db.query(Reminder)
        .filter(Reminder.reminder_time <= now, Reminder.is_sent == False)  # noqa: E712
        .all()
    )
