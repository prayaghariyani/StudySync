"""
Export helpers for turning tasks/exams into portable formats:

- CSV: for spreadsheets.
- iCalendar (.ics): importable into Google Calendar, Apple Calendar,
  Outlook, etc. This satisfies the plan's "Google Calendar export" goal
  without needing any paid API or OAuth flow — a standards-based .ics
  file is exactly what Google Calendar's "Import" feature consumes.
"""
import csv
import io
from datetime import timedelta
from icalendar import Calendar, Event

from app.models.task import Task
from app.models.exam import Exam


def tasks_and_exams_to_csv(tasks, exams) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Type", "Title", "Subject", "Date", "Priority", "Status/Duration", "Notes"])

    for t in tasks:
        writer.writerow([
            "Task",
            t.title,
            t.subject.name if t.subject else "",
            t.due_date.isoformat(),
            t.priority.value if hasattr(t.priority, "value") else t.priority,
            t.status.value if hasattr(t.status, "value") else t.status,
            (t.description or "").replace("\n", " "),
        ])

    for e in exams:
        writer.writerow([
            "Exam",
            e.title,
            e.subject.name if e.subject else "",
            e.exam_date.isoformat(),
            e.priority.value if hasattr(e.priority, "value") else e.priority,
            f"{e.duration} min",
            (e.notes or "").replace("\n", " "),
        ])

    return output.getvalue()


def tasks_and_exams_to_ics(tasks, exams) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//StudySync//studysync.app//")
    cal.add("version", "2.0")

    for t in tasks:
        event = Event()
        event.add("summary", f"[Task] {t.title}")
        event.add("dtstart", t.due_date)
        event.add("dtend", t.due_date + timedelta(minutes=30))
        event.add("description", t.description or "")
        event.add("uid", f"task-{t.id}@studysync")
        cal.add_component(event)

    for e in exams:
        event = Event()
        event.add("summary", f"[Exam] {e.title}")
        event.add("dtstart", e.exam_date)
        event.add("dtend", e.exam_date + timedelta(minutes=e.duration or 60))
        event.add("location", e.location or "")
        event.add("description", e.notes or "")
        event.add("uid", f"exam-{e.id}@studysync")
        cal.add_component(event)

    return cal.to_ical()
