import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base


class NotificationType(str, enum.Enum):
    browser = "Browser"
    in_app = "In-App"
    email = "Email"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)

    reminder_time = Column(DateTime, nullable=False)
    notification_type = Column(Enum(NotificationType), default=NotificationType.in_app)
    message = Column(String(255), nullable=True)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reminders")
    task = relationship("Task", back_populates="reminders")
    exam = relationship("Exam", back_populates="reminders")
