import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.models.task import Priority


class ExamType(str, enum.Enum):
    quiz = "quiz"
    mid_semester = "mid_semester"
    end_semester = "end_semester"
    practical = "practical"
    viva = "viva"
    other = "other"


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    exam_type = Column(Enum(ExamType), default=ExamType.other)
    exam_date = Column(DateTime, nullable=False)
    duration = Column(Integer, default=60)  # minutes
    location = Column(String(120), nullable=True)
    priority = Column(Enum(Priority), default=Priority.HIGH)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="exams")
    reminders = relationship("Reminder", back_populates="exam", cascade="all, delete-orphan")
