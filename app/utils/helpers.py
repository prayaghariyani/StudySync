"""
General-purpose helper functions shared across services.

Contains the "smart priority" algorithm: a small weighted-scoring
function that combines urgency (time left), importance (user-set
priority), and effort (estimated hours) into a single numeric score.
Higher score = should be worked on sooner. This is what the dashboard,
task lists, and study recommendations sort by.
"""
from datetime import datetime
from app.models.task import Priority

# Base weight per priority level. URGENT tasks get a strong head start.
PRIORITY_WEIGHTS = {
    Priority.LOW: 1.0,
    Priority.MEDIUM: 2.0,
    Priority.HIGH: 3.5,
    Priority.URGENT: 5.0,
}


def calculate_priority_score(due_date: datetime, priority: Priority, estimated_hours: float,
                              now: datetime = None) -> float:
    """
    Compute a priority score for sorting tasks.

    score = priority_weight * urgency_factor + effort_factor

    - urgency_factor grows sharply as the deadline approaches (and is
      capped/boosted for overdue items so they always float to the top).
    - effort_factor gives a small nudge to bigger tasks so they don't
      get buried by a pile of trivial 5-minute ones.
    """
    now = now or datetime.utcnow()
    priority_weight = PRIORITY_WEIGHTS.get(priority, 2.0)

    hours_remaining = (due_date - now).total_seconds() / 3600.0

    if hours_remaining <= 0:
        # Overdue: the longer it's overdue, the higher the score.
        urgency_factor = 10.0 + min(abs(hours_remaining) / 24.0, 10.0)
    elif hours_remaining <= 24:
        urgency_factor = 8.0
    elif hours_remaining <= 72:
        urgency_factor = 5.0
    elif hours_remaining <= 168:  # 1 week
        urgency_factor = 3.0
    else:
        # Decays gently the further out the deadline is.
        urgency_factor = max(0.5, 168.0 / hours_remaining)

    effort_factor = min(estimated_hours or 1.0, 10.0) * 0.1

    return round(priority_weight * urgency_factor + effort_factor, 2)


def days_between(start: datetime, end: datetime) -> int:
    return (end.date() - start.date()).days


def format_duration(minutes: int) -> str:
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"
