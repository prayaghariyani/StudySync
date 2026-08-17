import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base


class SessionStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration = Column(Integer, default=0)  # minutes, derived from start/end
    status = Column(Enum(SessionStatus), default=SessionStatus.PLANNED)
    notes = Column(Text, nullable=True)

    # Pomodoro tracking
    is_pomodoro = Column(Boolean, default=False)
    pomodoro_count = Column(Integer, default=0)  # number of 25-min cycles completed

    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="study_sessions")
