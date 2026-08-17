"""
Task service — business logic that sits between the API layer and the
database. Keeping this out of api/tasks.py means the same logic
(priority scoring, recurrence expansion, overdue detection) can be
reused by the dashboard, analytics, and scheduler without duplicating it.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.task import Task, TaskStatus
from app.utils.helpers import calculate_priority_score


def refresh_priority_score(task: Task) -> Task:
    task.priority_score = calculate_priority_score(task.due_date, task.priority, task.estimated_hours)
    return task


def mark_overdue_tasks(db: Session, user_subject_ids: List[int]) -> int:
    """Flip any TODO/IN_PROGRESS task whose due_date has passed to OVERDUE.
    Returns the number of tasks updated."""
    now = datetime.utcnow()
    overdue = (
        db.query(Task)
        .filter(
            Task.subject_id.in_(user_subject_ids),
            Task.due_date < now,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
        )
        .all()
    )
    for task in overdue:
        task.status = TaskStatus.OVERDUE
    if overdue:
        db.commit()
    return len(overdue)


def complete_task(db: Session, task: Task) -> Task:
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def generate_next_recurrence(task: Task) -> Optional[Task]:
    """
    If a completed task has a recurrence_rule, build the *next*
    occurrence as a fresh Task object (not yet added to the session).
    Returns None if there's no rule or the recurrence window has ended.
    """
    if not task.recurrence_rule:
        return None

    delta_map = {
        "DAILY": timedelta(days=1),
        "WEEKLY": timedelta(weeks=1),
        "MONTHLY": timedelta(days=30),
    }
    delta = delta_map.get(task.recurrence_rule.upper())
    if not delta:
        return None

    next_due = task.due_date + delta
    if task.recurrence_end_date and next_due > task.recurrence_end_date:
        return None

    return Task(
        subject_id=task.subject_id,
        title=task.title,
        description=task.description,
        type=task.type,
        priority=task.priority,
        status=TaskStatus.TODO,
        due_date=next_due,
        estimated_hours=task.estimated_hours,
        recurrence_rule=task.recurrence_rule,
        recurrence_end_date=task.recurrence_end_date,
        priority_score=calculate_priority_score(next_due, task.priority, task.estimated_hours),
    )


def get_due_soon(db: Session, subject_ids: List[int], within_hours: int = 72) -> List[Task]:
    now = datetime.utcnow()
    window_end = now + timedelta(hours=within_hours)
    return (
        db.query(Task)
        .filter(
            Task.subject_id.in_(subject_ids),
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
            Task.due_date.between(now, window_end),
        )
        .order_by(Task.due_date.asc())
        .all()
    )
