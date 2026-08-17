# StudySync

A smart semester planner for students — subjects, tasks, exams, study
sessions, reminders, and analytics, all in one self-hosted app.

## What it does

- **Subjects & semesters** — organize your term into subjects with credits, teachers, and color-coding.
- **Tasks** — assignments/projects/labs with priority, due dates, subtasks, and recurrence (daily/weekly/monthly). A weighted scoring algorithm (`app/utils/helpers.py::calculate_priority_score`) automatically ranks what needs attention first, based on urgency, importance, and effort.
- **Exams** — quizzes, mid-sems, end-sems, practicals, and vivas, each with reminders.
- **Calendar** — a unified month/week/day view (FullCalendar) merging tasks, exams, and study sessions.
- **Study sessions & Pomodoro** — log study time and run a built-in 25-minute Pomodoro timer.
- **Real-time notifications** — a WebSocket connection pushes reminders and overdue alerts straight to the browser, backed by an APScheduler job that checks every minute; falls back to browser Notifications and an in-app bell.
- **Analytics** — completion rate, on-time rate, study efficiency, per-subject performance, and a GitHub-style 90-day study heatmap.
- **Gamification** — XP, levels, and a daily study streak for completing tasks.
- **Export & backup** — CSV export, `.ics` calendar export (importable into Google/Apple/Outlook calendars), and a full JSON backup/restore of your data.
- **Command palette** — `⌘K` / `Ctrl+K` for fast navigation and actions.
- **Dark mode**, keyboard accessibility, and a responsive layout.

## Tech stack

| Layer      | Tech |
|------------|------|
| Backend    | FastAPI, SQLAlchemy, Pydantic v2 |
| Database   | SQLite (file-based, zero config) |
| Auth       | JWT (python-jose) + bcrypt password hashing |
| Realtime   | Native WebSockets + APScheduler background jobs |
| Frontend   | Plain HTML/CSS/JS (no build step), FullCalendar, Chart.js, Lucide icons |
| Tests      | Pytest + FastAPI's TestClient |

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for how the pieces fit together.

## Getting started

### 1. Prerequisites
- Python 3.10+

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Use SQLite for local development:

```bash
DATABASE_URL=sqlite:///./studysync.db
```

Use Neon Postgres in deployment:

```bash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@ep-xxxx.region.aws.neon.tech/DBNAME?sslmode=require
```

For Render, set `PYTHON_VERSION=3.12.10` in the dashboard or keep the
included `.python-version` file so deployment uses a version with
prebuilt wheels for core dependencies like `pydantic-core`.

### 4. Run the app

```bash
python run.py
```

or equivalently:

```bash
uvicorn app.main:app --reload
```

For Render, use this start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The app creates its SQLite database (`studysync.db`) automatically on
first run — no migrations to run.

### 5. Open it

- App: **http://localhost:8000**
- Interactive API docs (Swagger): **http://localhost:8000/docs**

Register an account on the sign-in page, create a semester, add a
subject, and you're off.

### 6. Run tests

```bash
pytest
```

## Configuration

Environment variables (all optional — sensible defaults are used for local dev):

| Variable | Default | Purpose |
|---|---|---|
| `STUDYSYNC_SECRET_KEY` | dev key baked into the repo | JWT signing secret — **set this in production** |
| `DATABASE_URL` | `sqlite:///./studysync.db` | SQLAlchemy connection string. Keep SQLite locally or set a Neon Postgres URL in deployment |

## Project layout

```
StudySync/
├── app/                  # FastAPI backend
│   ├── main.py            # App entrypoint, router wiring, static file serving
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── api/                 # HTTP route handlers, one file per resource
│   ├── services/            # Business logic (priority scoring, analytics, etc.)
│   ├── notifications/         # WebSocket manager + APScheduler background jobs
│   ├── database/               # Engine/session setup
│   └── utils/                    # Security, helpers, calendar export
├── frontend/              # Static HTML/CSS/JS (no build step)
│   ├── index.html          # Sign in / register
│   ├── dashboard.html        # SPA shell
│   ├── components/             # Reusable HTML partials (sidebar, navbar, task card)
│   ├── css/                      # Design tokens + component styles
│   └── js/                         # App logic, one file per feature area
├── tests/                 # Pytest suite
└── run.py                 # `python run.py` dev launcher
```

## Notes on scope

This is a full-featured but single-user-per-account, self-hosted
planner — there's no multi-tenant admin panel or paid integrations.
Email reminders are modeled in the data layer (`NotificationType.email`)
but not wired to an actual SMTP/email provider; in-app and browser
notifications are fully functional out of the box.
