from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.database import get_db
from app.models.exam import Exam
from app.models.subject import Subject
from app.models.semester import Semester
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamUpdate, ExamOut
from app.api.deps import get_current_user, get_user_subject_ids
from app.services.reminder_service import create_default_reminders_for_exam

router = APIRouter(prefix="/api/exams", tags=["exams"])


def _get_owned_exam(db: Session, exam_id: int, user_id: int) -> Exam:
    subject_ids = get_user_subject_ids(db, user_id)
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.subject_id.in_(subject_ids)).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


def _verify_subject_ownership(db: Session, subject_id: int, user_id: int):
    subject_ids = get_user_subject_ids(db, user_id)
    if subject_id not in subject_ids:
        raise HTTPException(status_code=404, detail="Subject not found")


@router.post("", response_model=ExamOut, status_code=201)
def create_exam(payload: ExamCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _verify_subject_ownership(db, payload.subject_id, current_user.id)
    exam = Exam(**payload.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    create_default_reminders_for_exam(db, current_user.id, exam)
    return exam


@router.get("", response_model=List[ExamOut])
def list_exams(subject_id: Optional[int] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject_ids = get_user_subject_ids(db, current_user.id)
    q = db.query(Exam).filter(Exam.subject_id.in_(subject_ids))
    if subject_id:
        q = q.filter(Exam.subject_id == subject_id)
    return q.order_by(Exam.exam_date.asc()).all()


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_exam(db, exam_id, current_user.id)


@router.patch("/{exam_id}", response_model=ExamOut)
def update_exam(exam_id: int, payload: ExamUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam = _get_owned_exam(db, exam_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    db.commit()
    db.refresh(exam)
    return exam


@router.delete("/{exam_id}", status_code=204)
def delete_exam(exam_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam = _get_owned_exam(db, exam_id, current_user.id)
    db.delete(exam)
    db.commit()
    return None
