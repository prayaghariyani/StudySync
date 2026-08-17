"""
Analytics service — computes the numbers behind the charts:
completion rate, on-time rate, study efficiency, per-subject
performance, and a GitHub-style study activity heatmap.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.study_session import StudySession, SessionStatus
from app.models.subject import Subject


def completion_rate(tasks: List[Task]) -> float:
    if not tasks:
        return 0.0
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    return round(len(completed) / len(tasks) * 100, 1)


def on_time_rate(tasks: List[Task]) -> float:
    """% of completed tasks finished before (or at) their due date."""
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED and t.completed_at]
    if not completed:
        return 0.0
    on_time = [t for t in completed if t.completed_at <= t.due_date]
    return round(len(on_time) / len(completed) * 100, 1)


def study_efficiency(tasks: List[Task], sessions: List[StudySession]) -> float:
    """Completed tasks per hour of logged study time."""
    completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    total_minutes = sum(s.duration or 0 for s in sessions if s.status == SessionStatus.COMPLETED)
    hours = total_minutes / 60.0
    if hours <= 0:
        return 0.0
    return round(completed / hours, 2)


def subject_performance(db: Session, subjects: List[Subject]) -> dict:
    """Completion rate per subject, e.g. {'OS': 84.0, 'DBMS': 72.0}."""
    result = {}
    for subj in subjects:
        tasks = db.query(Task).filter(Task.subject_id == subj.id).all()
        result[subj.name] = completion_rate(tasks)
    return result


def study_heatmap(sessions: List[StudySession], days: int = 90) -> List[dict]:
    """
    Aggregate completed study minutes per calendar day for the last
    `days` days — GitHub-contribution-graph style data.
    """
    since = datetime.utcnow() - timedelta(days=days)
    daily_minutes = defaultdict(int)

    for s in sessions:
        if s.status != SessionStatus.COMPLETED or s.start_time < since:
            continue
        day_key = s.start_time.date().isoformat()
        daily_minutes[day_key] += s.duration or 0

    return [{"date": day, "minutes": minutes} for day, minutes in sorted(daily_minutes.items())]


def semester_progress(tasks: List[Task]) -> dict:
    total = len(tasks)
    completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    overdue = len([t for t in tasks if t.status == TaskStatus.OVERDUE])
    in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
    todo = len([t for t in tasks if t.status == TaskStatus.TODO])
    return {
        "total": total,
        "completed": completed,
        "overdue": overdue,
        "in_progress": in_progress,
        "todo": todo,
        "percent_complete": round((completed / total * 100) if total else 0, 1),
    }
