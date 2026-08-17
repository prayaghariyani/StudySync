"""Shared dependencies used across API routers: DB session + current user."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id = payload.get("user_id")
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_user_subject_ids(db: Session, user_id: int) -> list:
    """All subject ids owned (transitively) by a user, used to scope every query."""
    from app.models.semester import Semester
    from app.models.subject import Subject
    semester_ids = [s.id for s in db.query(Semester.id).filter(Semester.user_id == user_id).all()]
    if not semester_ids:
        return []
    return [s.id for s in db.query(Subject.id).filter(Subject.semester_id.in_(semester_ids)).all()]
