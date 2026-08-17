from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.task import Task
from app.models.study_session import StudySession
from app.models.subject import Subject
from app.models.semester import Semester
from app.api.deps import get_current_user, get_user_subject_ids
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
def analytics_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject_ids = get_user_subject_ids(db, current_user.id)
    tasks = db.query(Task).filter(Task.subject_id.in_(subject_ids)).all()
    sessions = db.query(StudySession).filter(StudySession.subject_id.in_(subject_ids)).all()
    subjects = db.query(Subject).filter(Subject.id.in_(subject_ids)).all()

    return {
        "completion_rate": analytics_service.completion_rate(tasks),
        "on_time_rate": analytics_service.on_time_rate(tasks),
        "study_efficiency": analytics_service.study_efficiency(tasks, sessions),
        "subject_performance": analytics_service.subject_performance(db, subjects),
        "semester_progress": analytics_service.semester_progress(tasks),
        "xp": current_user.xp,
        "level": current_user.level,
        "streak_days": current_user.streak_days,
    }


@router.get("/heatmap")
def analytics_heatmap(days: int = 90, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject_ids = get_user_subject_ids(db, current_user.id)
    sessions = db.query(StudySession).filter(StudySession.subject_id.in_(subject_ids)).all()
    return analytics_service.study_heatmap(sessions, days=days)
