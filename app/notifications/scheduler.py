"""
Background scheduler.

Uses APScheduler's AsyncIOScheduler (so jobs can `await` the WebSocket
manager directly, since the whole app runs on FastAPI's asyncio event
loop). Two recurring jobs:

1. check_due_reminders — every 60s, finds reminders whose time has
   arrived, pushes them over WebSocket to the owning user, and marks
   them as sent.
2. sweep_overdue_tasks — every 5 minutes, flips any task whose
   due_date has passed from TODO/IN_PROGRESS to OVERDUE.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.database import SessionLocal
from app.models.task import Task, TaskStatus
from app.services.reminder_service import get_due_reminders
from app.notifications.websocket import manager

logger = logging.getLogger("studysync.scheduler")
scheduler = AsyncIOScheduler()


async def check_due_reminders():
    db = SessionLocal()
    try:
        due = get_due_reminders(db)
        for reminder in due:
            payload = {
                "type": "reminder",
                "id": reminder.id,
                "message": reminder.message or "You have a reminder",
                "task_id": reminder.task_id,
                "exam_id": reminder.exam_id,
            }
            await manager.send_to_user(reminder.user_id, payload)
            reminder.is_sent = True
        if due:
            db.commit()
    except Exception:
        logger.exception("Error while checking due reminders")
    finally:
        db.close()


async def sweep_overdue_tasks():
    db = SessionLocal()
    try:
        from datetime import datetime
        now = datetime.utcnow()
        overdue_tasks = (
            db.query(Task)
            .filter(Task.due_date < now, Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]))
            .all()
        )
        for task in overdue_tasks:
            task.status = TaskStatus.OVERDUE
            # Notify the owning user via their subject -> semester -> user chain.
            try:
                user_id = task.subject.semester.user_id
                await manager.send_to_user(user_id, {
                    "type": "overdue",
                    "message": f"'{task.title}' is now overdue",
                    "task_id": task.id,
                })
            except Exception:
                pass
        if overdue_tasks:
            db.commit()
    except Exception:
        logger.exception("Error while sweeping overdue tasks")
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_due_reminders, "interval", seconds=60, id="check_due_reminders", replace_existing=True)
        scheduler.add_job(sweep_overdue_tasks, "interval", minutes=5, id="sweep_overdue_tasks", replace_existing=True)
        scheduler.start()
        logger.info("Background scheduler started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
