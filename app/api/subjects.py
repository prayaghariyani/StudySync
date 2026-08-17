from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.subject import Subject
from app.models.semester import Semester
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


def _verify_semester_ownership(db: Session, semester_id: int, user_id: int):
    semester = db.query(Semester).filter(Semester.id == semester_id, Semester.user_id == user_id).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    return semester


def _get_owned_subject(db: Session, subject_id: int, user_id: int) -> Subject:
    subject = (
        db.query(Subject)
        .join(Semester, Subject.semester_id == Semester.id)
        .filter(Subject.id == subject_id, Semester.user_id == user_id)
        .first()
    )
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.post("", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _verify_semester_ownership(db, payload.semester_id, current_user.id)
    subject = Subject(**payload.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("", response_model=List[SubjectOut])
def list_subjects(semester_id: int = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Subject).join(Semester, Subject.semester_id == Semester.id).filter(Semester.user_id == current_user.id)
    if semester_id:
        q = q.filter(Subject.semester_id == semester_id)
    return q.all()


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_subject(db, subject_id, current_user.id)


@router.patch("/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, payload: SubjectUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject = _get_owned_subject(db, subject_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=204)
def delete_subject(subject_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject = _get_owned_subject(db, subject_id, current_user.id)
    db.delete(subject)
    db.commit()
    return None
