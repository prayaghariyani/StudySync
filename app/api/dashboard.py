from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.exam import Exam
from app.models.subject import Subject
from app.api.deps import get_current_user, get_user_subject_ids
from app.services.task_service import mark_overdue_tasks, get_due_soon
from app.services.analytics_service import semester_progress

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject_ids = get_user_subject_ids(db, current_user.id)
    mark_overdue_tasks(db, subject_ids)

    now = datetime.utcnow()
    today_end = datetime.combine(now.date(), datetime.max.time())

    today_tasks = (
        db.query(Task)
        .filter(Task.subject_id.in_(subject_ids), Task.due_date.between(now.replace(hour=0, minute=0, second=0), today_end))
        .order_by(Task.due_date.asc())
        .all()
    )

    due_soon = get_due_soon(db, subject_ids, within_hours=72)

    upcoming_exams = (
        db.query(Exam)
        .filter(Exam.subject_id.in_(subject_ids), Exam.exam_date >= now)
        .order_by(Exam.exam_date.asc())
        .limit(5)
        .all()
    )

    all_tasks = db.query(Task).filter(Task.subject_id.in_(subject_ids)).all()

    return {
        "greeting_counts": {
            "subjects": len(subject_ids),
            "tasks": len([t for t in all_tasks if t.status != TaskStatus.COMPLETED]),
            "exams": db.query(Exam).filter(Exam.subject_id.in_(subject_ids), Exam.exam_date >= now).count(),
        },
        "today": [
            {"id": t.id, "title": t.title, "due_date": t.due_date.isoformat(), "status": t.status.value, "priority": t.priority.value}
            for t in today_tasks
        ],
        "due_soon": [
            {"id": t.id, "title": t.title, "due_date": t.due_date.isoformat(), "priority": t.priority.value}
            for t in due_soon
        ],
        "upcoming_exams": [
            {"id": e.id, "title": e.title, "exam_date": e.exam_date.isoformat(), "location": e.location}
            for e in upcoming_exams
        ],
        "progress": semester_progress(all_tasks),
    }
