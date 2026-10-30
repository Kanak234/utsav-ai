"""Typed data models shared across the app.

Why dataclasses: they give us clear field names, type hints and immutability
(`frozen=True`) with zero extra dependencies. Every module passes these objects
around instead of loose dicts, so a typo in a key becomes an error early.
Flow: validation.py creates EventInput -> planner.py fills a Plan -> app.py / export.py read it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class EventType(str, Enum):
    """The three event families named in the problem statement."""

    WEDDING = "Wedding"
    BIRTHDAY = "Birthday"
    COMMUNITY = "Community Event"


@dataclass(frozen=True)
class EventInput:
    """Everything the user tells us about their event (already validated)."""

    event_type: EventType
    event_name: str
    city: str
    event_date: date
    guests: int
    budget_inr: int
    theme: str = ""
    preferences: str = ""


@dataclass(frozen=True)
class BudgetLine:
    """One budget category, e.g. 'Venue' -> ₹1,50,000 (30%)."""

    category: str
    amount_inr: int
    percent: float


@dataclass(frozen=True)
class TimelineItem:
    """One dated task in the countdown, e.g. 'Book venue' due 2026-11-20."""

    due: date
    task: str
    days_before: int
    overdue: bool = False


@dataclass(frozen=True)
class VendorItem:
    """One vendor to book plus the questions worth asking them."""

    vendor: str
    budget_inr: int
    questions: tuple[str, ...]


@dataclass(frozen=True)
class Ideas:
    """Personalised creative ideas (from Gemini, or the offline fallback)."""

    theme_concept: str
    decor: tuple[str, ...]
    food: tuple[str, ...]
    activities: tuple[str, ...]
    money_saving_tips: tuple[str, ...]
    source: str  # "gemini" or "offline" — shown in the UI for transparency


@dataclass
class Plan:
    """The full plan the UI renders and the exporters write out."""

    event: EventInput
    budget: list[BudgetLine]
    per_guest_inr: int
    timeline: list[TimelineItem]
    vendors: list[VendorItem]
    ideas: Ideas
    warnings: list[str] = field(default_factory=list)
