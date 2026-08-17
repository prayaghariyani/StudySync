"""
Database configuration module.

Sets up the SQLAlchemy engine, session factory, and declarative base
used across the whole application. SQLite is used as the storage
engine (file-based, zero-config, perfect for a single-user academic
planner) but the code only relies on standard SQLAlchemy features so
swapping to Postgres/MySQL later just means changing DATABASE_URL.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'studysync.db')}")

# check_same_thread=False is required because SQLite by default only
# allows the thread that created a connection to use it, but FastAPI
# handles each request in its own thread from a pool.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Imports models first so they register with Base."""
    from app.models import user, semester, subject, task, exam, study_session, reminder  # noqa: F401
    Base.metadata.create_all(bind=engine)
