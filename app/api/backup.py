"""
Backup / restore.

Exports the user's entire dataset (semesters, subjects, tasks, exams,
study sessions) as one JSON document, and can restore from that same
document. This is a simple, dependency-free way to satisfy the plan's
"Backup/restore" utility without needing cloud storage.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.semester import Semester
from app.models.subject import Subject
from app.models.task import Task
from app.models.exam import Exam
from app.models.study_session import StudySession
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/backup", tags=["backup"])


def _serialize_dt(value):
    return value.isoformat() if value else None


@router.get("/export")
def export_backup(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    semesters = db.query(Semester).filter(Semester.user_id == current_user.id).all()
    data = {"version": 1, "exported_at": datetime.utcnow().isoformat(), "semesters": []}

    for sem in semesters:
        sem_data = {
            "name": sem.name,
            "start_date": sem.start_date.isoformat(),
            "end_date": sem.end_date.isoformat(),
            "is_active": sem.is_active,
            "subjects": [],
        }
        for subj in sem.subjects:
            subj_data = {
                "name": subj.name, "code": subj.code, "teacher": subj.teacher,
                "credits": subj.credits, "color": subj.color,
                "tasks": [], "exams": [], "study_sessions": [],
            }
            for t in subj.tasks:
                subj_data["tasks"].append({
                    "title": t.title, "description": t.description,
                    "type": t.type.value if hasattr(t.type, "value") else t.type,
                    "priority": t.priority.value if hasattr(t.priority, "value") else t.priority,
                    "status": t.status.value if hasattr(t.status, "value") else t.status,
                    "due_date": _serialize_dt(t.due_date),
                    "estimated_hours": t.estimated_hours,
                })
            for e in subj.exams:
                subj_data["exams"].append({
                    "title": e.title,
                    "exam_type": e.exam_type.value if hasattr(e.exam_type, "value") else e.exam_type,
                    "exam_date": _serialize_dt(e.exam_date),
                    "duration": e.duration, "location": e.location, "notes": e.notes,
                })
            for s in subj.study_sessions:
                subj_data["study_sessions"].append({
                    "title": s.title, "start_time": _serialize_dt(s.start_time),
                    "end_time": _serialize_dt(s.end_time), "duration": s.duration,
                })
            sem_data["subjects"].append(subj_data)
        data["semesters"].append(sem_data)

    return data


@router.post("/restore")
def restore_backup(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.get("version") != 1:
        raise HTTPException(status_code=400, detail="Unsupported backup file version")

    from datetime import date as date_cls
    created_semesters = 0
    for sem_data in payload.get("semesters", []):
        semester = Semester(
            user_id=current_user.id,
            name=sem_data["name"],
            start_date=date_cls.fromisoformat(sem_data["start_date"]),
            end_date=date_cls.fromisoformat(sem_data["end_date"]),
            is_active=sem_data.get("is_active", True),
        )
        db.add(semester)
        db.flush()  # get semester.id without committing yet
        created_semesters += 1

        for subj_data in sem_data.get("subjects", []):
            subject = Subject(
                semester_id=semester.id, name=subj_data["name"], code=subj_data.get("code"),
                teacher=subj_data.get("teacher"), credits=subj_data.get("credits", 0),
                color=subj_data.get("color", "#6366f1"),
            )
            db.add(subject)
            db.flush()

            for t in subj_data.get("tasks", []):
                db.add(Task(
                    subject_id=subject.id, title=t["title"], description=t.get("description"),
                    type=t.get("type", "other"), priority=t.get("priority", "MEDIUM"),
                    status=t.get("status", "TODO"), due_date=datetime.fromisoformat(t["due_date"]),
                    estimated_hours=t.get("estimated_hours", 1.0),
                ))
            for e in subj_data.get("exams", []):
                db.add(Exam(
                    subject_id=subject.id, title=e["title"], exam_type=e.get("exam_type", "other"),
                    exam_date=datetime.fromisoformat(e["exam_date"]), duration=e.get("duration", 60),
                    location=e.get("location"), notes=e.get("notes"),
                ))
            for s in subj_data.get("study_sessions", []):
                db.add(StudySession(
                    subject_id=subject.id, title=s["title"],
                    start_time=datetime.fromisoformat(s["start_time"]),
                    end_time=datetime.fromisoformat(s["end_time"]), duration=s.get("duration", 0),
                ))

    db.commit()
    return {"restored_semesters": created_semesters}
