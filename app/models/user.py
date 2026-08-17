from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    xp = Column(Integer, default=0)              # gamification: experience points
    level = Column(Integer, default=1)            # gamification: current level
    streak_days = Column(Integer, default=0)       # consecutive study-activity days
    last_active_date = Column(String(10), nullable=True)  # ISO date, used to compute streaks
    theme = Column(String(10), default="light")    # 'light' or 'dark', persisted per user
    created_at = Column(DateTime, default=datetime.utcnow)

    semesters = relationship("Semester", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
