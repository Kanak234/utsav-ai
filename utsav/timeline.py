"""Countdown timeline builder.

Why: the problem statement asks for timelines. We convert fixed
"N days before" milestones into real calendar dates. If the event is sooner
than a milestone allows, the task isn't dropped — it is scheduled for today
and flagged `overdue`, so a last-minute planner still sees everything.
Flow: planner.py -> build_timeline() -> list[TimelineItem] -> app.py + export.py (.ics)
"""

from __future__ import annotations

from datetime import date, timedelta

from .constants import TIMELINE_TASKS
from .models import EventType, TimelineItem


def build_timeline(event_type: EventType, event_date: date, today: date | None = None) -> list[TimelineItem]:
    """Return tasks sorted by due date (nearest first after compression)."""
    today = today or date.today()
    items: list[TimelineItem] = []
    for days_before, task in TIMELINE_TASKS[event_type]:
        ideal = event_date - timedelta(days=days_before)
        overdue = ideal < today
        items.append(
            TimelineItem(
                due=today if overdue else ideal,
                task=task,
                days_before=days_before,
                overdue=overdue,
            )
        )
    # Stable sort keeps the original priority order for tasks moved to "today".
    return sorted(items, key=lambda item: item.due)


def days_left(event_date: date, today: date | None = None) -> int:
    """Whole days from today until the event (0 on the day itself)."""
    return (event_date - (today or date.today())).days
