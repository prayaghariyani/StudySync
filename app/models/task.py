import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship, backref
from app.database.database import Base


class TaskType(str, enum.Enum):
    assignment = "assignment"
    project = "project"
    lab = "lab"
    homework = "homework"
    other = "other"


class Priority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # set for subtasks

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(TaskType), default=TaskType.other)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    due_date = Column(DateTime, nullable=False)
    estimated_hours = Column(Float, default=1.0)

    # Recurrence: simple rule string like "DAILY", "WEEKLY", "MONTHLY", or None
    recurrence_rule = Column(String(20), nullable=True)
    recurrence_end_date = Column(DateTime, nullable=True)

    # Computed/cached priority score from the smart priority algorithm
    priority_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    subject = relationship("Subject", back_populates="tasks")
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan")

    # Self-referential adjacency-list relationship for subtasks.
    # `remote_side=[id]` marks the "one" side (the parent), so `subtasks`
    # on a Task gives its children and `.parent` (via backref) gives its parent.
    subtasks = relationship(
        "Task",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
    )
