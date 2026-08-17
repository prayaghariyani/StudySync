"""
StudySync — FastAPI application entrypoint.

Responsibilities:
- Create DB tables on startup (init_db).
- Register every API router (auth, semesters, subjects, tasks, exams,
  study_sessions, reminders, calendar, analytics, dashboard, export, backup).
- Register the WebSocket notifications route.
- Start/stop the APScheduler background jobs with the app lifecycle.
- Serve the static frontend (HTML/CSS/JS) so the whole app runs from
  a single `uvicorn app.main:app` process — no separate frontend server needed.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database.database import init_db
from app.notifications.scheduler import start_scheduler, stop_scheduler
from app.notifications.ws_router import router as ws_router

from app.api.auth import router as auth_router
from app.api.semesters import router as semesters_router
from app.api.subjects import router as subjects_router
from app.api.tasks import router as tasks_router
from app.api.exams import router as exams_router
from app.api.study_sessions import router as study_sessions_router
from app.api.reminders import router as reminders_router
from app.api.calendar import router as calendar_router
from app.api.analytics import router as analytics_router
from app.api.dashboard import router as dashboard_router
from app.api.export import router as export_router
from app.api.backup import router as backup_router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="StudySync API",
    description="A smart semester planner: subjects, tasks, exams, study sessions, "
                "reminders, real-time notifications, and analytics.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS is permissive by default since the frontend is served from the same
# origin in normal use; kept open for local development against a separate
# dev server (e.g. `python -m http.server` on the frontend/ folder).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    auth_router, semesters_router, subjects_router, tasks_router, exams_router,
    study_sessions_router, reminders_router, calendar_router, analytics_router,
    dashboard_router, export_router, backup_router,
]:
    app.include_router(router)

app.include_router(ws_router)

# Serve frontend static assets (css/js/components) and the HTML entrypoints.
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
app.mount("/components", StaticFiles(directory=os.path.join(FRONTEND_DIR, "components")), name="components")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.api_route("/dashboard.html", methods=["GET", "HEAD"], include_in_schema=False)
def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


@app.api_route("/health", methods=["GET", "HEAD"], tags=["meta"])
def health_check():
    return {"status": "ok", "service": "StudySync"}
