"""
Calendar service — turns tasks, exams, and study sessions into a
unified list of "events" shaped for FullCalendar on the frontend.
"""
from typing import List
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.exam import Exam
from app.models.study_session import StudySession
from app.models.subject import Subject


def get_calendar_events(db: Session, subject_ids: List[int], start=None, end=None) -> List[dict]:
    events = []

    task_q = db.query(Task).filter(Task.subject_id.in_(subject_ids))
    exam_q = db.query(Exam).filter(Exam.subject_id.in_(subject_ids))
    session_q = db.query(StudySession).filter(StudySession.subject_id.in_(subject_ids))

    if start and end:
        task_q = task_q.filter(Task.due_date.between(start, end))
        exam_q = exam_q.filter(Exam.exam_date.between(start, end))
        session_q = session_q.filter(StudySession.start_time.between(start, end))

    for t in task_q.all():
        events.append({
            "id": f"task-{t.id}",
            "title": f"📝 {t.title}",
            "start": t.due_date.isoformat(),
            "allDay": False,
            "color": t.subject.color if t.subject else "#6366f1",
            "type": "task",
            "status": t.status.value if hasattr(t.status, "value") else t.status,
            "priority": t.priority.value if hasattr(t.priority, "value") else t.priority,
            "subject": t.subject.name if t.subject else None,
            "ref_id": t.id,
        })

    for e in exam_q.all():
        events.append({
            "id": f"exam-{e.id}",
            "title": f"🧪 {e.title}",
            "start": e.exam_date.isoformat(),
            "allDay": False,
            "color": "#ef4444",
            "type": "exam",
            "location": e.location,
            "subject": e.subject.name if e.subject else None,
            "ref_id": e.id,
        })

    for s in session_q.all():
        events.append({
            "id": f"session-{s.id}",
            "title": f"📖 {s.title}",
            "start": s.start_time.isoformat(),
            "end": s.end_time.isoformat(),
            "allDay": False,
            "color": "#10b981",
            "type": "study_session",
            "status": s.status.value if hasattr(s.status, "value") else s.status,
            "subject": s.subject.name if s.subject else None,
            "ref_id": s.id,
        })

    return events
