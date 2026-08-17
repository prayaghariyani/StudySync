# Architecture

## Overview

StudySync is a monolithic FastAPI application: one Python process
serves both the JSON API and the static frontend, backed by SQLite.
There's no separate frontend build/deploy step — `frontend/` is plain
HTML/CSS/JS mounted as static files by FastAPI itself. This keeps the
whole app runnable with a single `python run.py`.

```
Browser  <── HTTP (REST) ──>  FastAPI app  <── SQLAlchemy ──>  SQLite
   │
   └──── WebSocket (/ws/notifications) ────>  ConnectionManager
                                                     ▲
                                              APScheduler jobs
                                          (reminders, overdue sweep)
```

## Backend layers

The backend follows a fairly standard layered structure, each layer
only talking to the one below it:

1. **`app/api/`** — FastAPI routers. One file per resource
   (`auth.py`, `subjects.py`, `tasks.py`, `exams.py`,
   `study_sessions.py`, `reminders.py`, `calendar.py`, `analytics.py`,
   `dashboard.py`, `export.py`, `backup.py`, plus `semesters.py` as
   the parent resource of subjects). Routers handle HTTP concerns —
   request parsing, auth checks, status codes — and delegate real
   logic to `services/`.

2. **`app/services/`** — business logic that doesn't belong in a
   route handler:
   - `task_service.py` — priority scoring, overdue detection, recurrence expansion.
   - `reminder_service.py` — creating default reminders, finding due ones.
   - `calendar_service.py` — merges tasks/exams/study sessions into one event feed for FullCalendar.
   - `analytics_service.py` — completion rate, on-time rate, study efficiency, heatmap data.

3. **`app/models/`** — SQLAlchemy ORM models (one table each): `User`,
   `Semester`, `Subject`, `Task`, `Exam`, `StudySession`, `Reminder`.

4. **`app/schemas/`** — Pydantic models for request validation and
   response shaping. Kept separate from ORM models so the API's public
   contract can evolve independently of the DB schema.

5. **`app/database/`** — SQLAlchemy engine/session setup and the
   `get_db()` FastAPI dependency.

6. **`app/utils/`** — stateless helpers: `security.py` (JWT + bcrypt),
   `helpers.py` (the priority-scoring formula), `calendar_export.py`
   (CSV/.ics generation).

7. **`app/notifications/`** — everything real-time:
   - `websocket.py` — an in-memory `ConnectionManager` mapping `user_id -> [WebSocket]`.
   - `scheduler.py` — an `AsyncIOScheduler` running two jobs: check due reminders every 60s, sweep overdue tasks every 5 minutes.
   - `ws_router.py` — the `/ws/notifications` endpoint (JWT passed as a query param, since browsers can't set headers on a WS handshake).
   - `browser_notifications.py` — shapes a payload for the frontend's `Notification` API.

## Data model

```
User ──1:N── Semester ──1:N── Subject ──1:N── Task (self-referential for subtasks)
                                        ├──1:N── Exam
                                        └──1:N── StudySession
User ──1:N── Reminder (optionally linked to a Task or an Exam)
```

Every query in `app/api/` is scoped to the authenticated user by
walking this chain (`get_user_subject_ids` in `app/api/deps.py`) — a
user can only ever see semesters/subjects/tasks/exams/sessions that
trace back to their own `user_id`. There's no separate "is this mine"
check scattered everywhere; ownership is enforced by construction.

## Why these choices

- **SQLite over Postgres**: this is a single-user, self-hosted app —
  SQLite means zero setup (no separate DB server) while the code only
  uses standard SQLAlchemy, so swapping `DATABASE_URL` to Postgres
  later needs no code changes.
- **JWT over sessions**: stateless auth means the WebSocket endpoint
  can validate a token the same way the REST endpoints do, without a
  shared session store.
- **Priority score is a real algorithm, not a sort key alias**: see
  `calculate_priority_score()` in `app/utils/helpers.py`. It combines
  a priority weight, a non-linear urgency curve (overdue and
  due-within-24h tasks jump to the top), and a small effort factor —
  computed on every create/update and re-sortable at query time via
  the cached `priority_score` column.
- **No frontend framework**: the scope (SPA-ish dashboard, calendar,
  charts, forms) doesn't need React/Vue's overhead. Vanilla JS keeps
  the "how do I run this" answer to one command, with FullCalendar and
  Chart.js pulled in via CDN for the two things that genuinely benefit
  from a library.

## Frontend structure

`frontend/dashboard.html` is a single-page shell: it loads
`components/sidebar.html` and `components/navbar.html` via `fetch()`,
then `js/dashboard.js` acts as a tiny hash-based router
(`#dashboard`, `#tasks`, `#exams`, `#calendar`, `#sessions`,
`#subjects`, `#analytics`, `#settings`) that swaps the contents of
`#main-content`. Each view's rendering logic lives in the JS file most
relevant to it (`tasks.js`, `calendar.js`, or inline in
`dashboard.js` for the smaller views). `app.js` holds cross-cutting
concerns used by every view: the `api()` fetch wrapper (attaches the
JWT, handles 401s), toasts, theme switching, and the `⌘K` command
palette.

## Real-time notification flow

1. On login, the frontend opens `wss://.../ws/notifications?token=<jwt>`.
2. Every 60 seconds, `scheduler.py`'s `check_due_reminders` job queries
   for reminders whose `reminder_time` has passed and `is_sent` is
   false, pushes each one to the owning user's open WebSocket(s) via
   `ConnectionManager.send_to_user`, and marks it sent.
3. The frontend's `notifications.js` shows a toast and, if the tab
   isn't focused, a browser `Notification`.
4. `GET /api/reminders/pending` is polled once on page load as a
   fallback, in case reminders fired while the browser was closed.

## Testing

`tests/test_api.py` uses FastAPI's `TestClient` against a temporary
SQLite file (set via `DATABASE_URL` before the app is imported), so
tests never touch your real `studysync.db`. It covers the
register → login → create semester → subject → task → complete → XP
flow end to end, plus auth-rejection cases.
