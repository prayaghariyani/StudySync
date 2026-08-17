from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from app.database.database import get_db
from app.models.task import Task, TaskStatus
from app.models.subject import Subject
from app.models.semester import Semester
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut, TaskWithSubtasks
from app.api.deps import get_current_user, get_user_subject_ids
from app.services.task_service import refresh_priority_score, complete_task, generate_next_recurrence
from app.services.reminder_service import create_default_reminders_for_task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_owned_task(db: Session, task_id: int, user_id: int) -> Task:
    subject_ids = get_user_subject_ids(db, user_id)
    task = db.query(Task).filter(Task.id == task_id, Task.subject_id.in_(subject_ids)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _verify_subject_ownership(db: Session, subject_id: int, user_id: int):
    subject_ids = get_user_subject_ids(db, user_id)
    if subject_id not in subject_ids:
        raise HTTPException(status_code=404, detail="Subject not found")


def _award_xp_and_streak(db: Session, user: User, amount: int = 10):
    """Small gamification hook: completing a task grants XP, levels up
    every 100 XP, and bumps a daily streak counter."""
    user.xp = (user.xp or 0) + amount
    user.level = 1 + (user.xp // 100)

    today = date.today().isoformat()
    if user.last_active_date != today:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        if user.last_active_date == yesterday:
            user.streak_days = (user.streak_days or 0) + 1
        else:
            user.streak_days = 1
        user.last_active_date = today
    db.commit()


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _verify_subject_ownership(db, payload.subject_id, current_user.id)
    task = Task(**payload.model_dump())
    refresh_priority_score(task)
    db.add(task)
    db.commit()
    db.refresh(task)
    create_default_reminders_for_task(db, current_user.id, task)
    return task


@router.get("", response_model=List[TaskOut])
def list_tasks(
    subject_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject_ids = get_user_subject_ids(db, current_user.id)
    q = db.query(Task).filter(Task.subject_id.in_(subject_ids), Task.parent_task_id.is_(None))
    if subject_id:
        q = q.filter(Task.subject_id == subject_id)
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == priority)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Task.title.ilike(like), Task.description.ilike(like)))
    return q.order_by(Task.priority_score.desc()).all()


@router.get("/{task_id}", response_model=TaskWithSubtasks)
def get_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_task(db, task_id, current_user.id)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = _get_owned_task(db, task_id, current_user.id)
    if payload.subject_id is not None:
        _verify_subject_ownership(db, payload.subject_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    refresh_priority_score(task)
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/complete", response_model=TaskOut)
def complete_task_endpoint(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = _get_owned_task(db, task_id, current_user.id)
    task = complete_task(db, task)
    _award_xp_and_streak(db, current_user, amount=10)

    next_task = generate_next_recurrence(task)
    if next_task:
        db.add(next_task)
        db.commit()

    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = _get_owned_task(db, task_id, current_user.id)
    db.delete(task)
    db.commit()
    return None
