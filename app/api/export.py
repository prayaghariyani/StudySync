from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.database.database import get_db
from app.models.user import User
from app.models.task import Task
from app.models.exam import Exam
from app.api.deps import get_current_user, get_user_subject_ids
from app.utils.calendar_export import tasks_and_exams_to_csv, tasks_and_exams_to_ics

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/csv")
def export_csv(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject_ids = get_user_subject_ids(db, current_user.id)
    tasks = db.query(Task).filter(Task.subject_id.in_(subject_ids)).all()
    exams = db.query(Exam).filter(Exam.subject_id.in_(subject_ids)).all()
    csv_data = tasks_and_exams_to_csv(tasks, exams)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=studysync_export.csv"},
    )


@router.get("/ics")
def export_ics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject_ids = get_user_subject_ids(db, current_user.id)
    tasks = db.query(Task).filter(Task.subject_id.in_(subject_ids)).all()
    exams = db.query(Exam).filter(Exam.subject_id.in_(subject_ids)).all()
    ics_bytes = tasks_and_exams_to_ics(tasks, exams)
    return StreamingResponse(
        io.BytesIO(ics_bytes),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=studysync_calendar.ics"},
    )
