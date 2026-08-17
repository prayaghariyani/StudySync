from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.database import get_db
from app.models.study_session import StudySession, SessionStatus
from app.models.user import User
from app.schemas.study_session import StudySessionCreate, StudySessionUpdate, StudySessionOut
from app.api.deps import get_current_user, get_user_subject_ids

router = APIRouter(prefix="/api/study-sessions", tags=["study_sessions"])


def _get_owned_session(db: Session, session_id: int, user_id: int) -> StudySession:
    subject_ids = get_user_subject_ids(db, user_id)
    s = db.query(StudySession).filter(StudySession.id == session_id, StudySession.subject_id.in_(subject_ids)).first()
    if not s:
        raise HTTPException(status_code=404, detail="Study session not found")
    return s


def _verify_subject_ownership(db: Session, subject_id: int, user_id: int):
    subject_ids = get_user_subject_ids(db, user_id)
    if subject_id not in subject_ids:
        raise HTTPException(status_code=404, detail="Subject not found")


@router.post("", response_model=StudySessionOut, status_code=201)
def create_session(payload: StudySessionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _verify_subject_ownership(db, payload.subject_id, current_user.id)
    duration = int((payload.end_time - payload.start_time).total_seconds() // 60)
    session = StudySession(**payload.model_dump(), duration=max(duration, 0))
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=List[StudySessionOut])
def list_sessions(subject_id: Optional[int] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject_ids = get_user_subject_ids(db, current_user.id)
    q = db.query(StudySession).filter(StudySession.subject_id.in_(subject_ids))
    if subject_id:
        q = q.filter(StudySession.subject_id == subject_id)
    return q.order_by(StudySession.start_time.desc()).all()


@router.patch("/{session_id}", response_model=StudySessionOut)
def update_session(session_id: int, payload: StudySessionUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = _get_owned_session(db, session_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    if payload.start_time or payload.end_time:
        session.duration = max(int((session.end_time - session.start_time).total_seconds() // 60), 0)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/complete", response_model=StudySessionOut)
def complete_session(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = _get_owned_session(db, session_id, current_user.id)
    session.status = SessionStatus.COMPLETED
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/pomodoro-tick", response_model=StudySessionOut)
def pomodoro_tick(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Called by the frontend timer each time a 25-minute Pomodoro cycle completes."""
    session = _get_owned_session(db, session_id, current_user.id)
    session.pomodoro_count = (session.pomodoro_count or 0) + 1
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = _get_owned_session(db, session_id, current_user.id)
    db.delete(session)
    db.commit()
    return None
