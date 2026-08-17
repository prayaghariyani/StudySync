from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    name = Column(String(120), nullable=False)
    code = Column(String(40), nullable=True)
    teacher = Column(String(120), nullable=True)
    credits = Column(Integer, default=0)
    color = Column(String(20), default="#6366f1")  # hex color used across UI/calendar
    created_at = Column(DateTime, default=datetime.utcnow)

    semester = relationship("Semester", back_populates="subjects")
    tasks = relationship("Task", back_populates="subject", cascade="all, delete-orphan")
    exams = relationship("Exam", back_populates="subject", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="subject", cascade="all, delete-orphan")
