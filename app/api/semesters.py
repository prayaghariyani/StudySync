from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.semester import Semester
from app.models.user import User
from app.schemas.semester import SemesterCreate, SemesterUpdate, SemesterOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/semesters", tags=["semesters"])


@router.post("", response_model=SemesterOut, status_code=201)
def create_semester(payload: SemesterCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    semester = Semester(user_id=current_user.id, **payload.model_dump())
    db.add(semester)
    db.commit()
    db.refresh(semester)
    return semester


@router.get("", response_model=List[SemesterOut])
def list_semesters(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Semester).filter(Semester.user_id == current_user.id).order_by(Semester.start_date.desc()).all()


@router.get("/{semester_id}", response_model=SemesterOut)
def get_semester(semester_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    semester = db.query(Semester).filter(Semester.id == semester_id, Semester.user_id == current_user.id).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    return semester


@router.patch("/{semester_id}", response_model=SemesterOut)
def update_semester(semester_id: int, payload: SemesterUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    semester = db.query(Semester).filter(Semester.id == semester_id, Semester.user_id == current_user.id).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(semester, field, value)
    db.commit()
    db.refresh(semester)
    return semester


@router.delete("/{semester_id}", status_code=204)
def delete_semester(semester_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    semester = db.query(Semester).filter(Semester.id == semester_id, Semester.user_id == current_user.id).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    db.delete(semester)
    db.commit()
    return None
