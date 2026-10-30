"""Orchestrator: turns one validated EventInput into a complete Plan.

Why a separate module: app.py stays pure UI and this function stays pure
logic, so the whole planning pipeline can be unit-tested without Streamlit.
Flow: app.py -> create_plan() -> budget + timeline + checklist + ai -> Plan
"""

from __future__ import annotations

from datetime import date

from .ai import TextGenerator, generate_ideas
from .budget import allocate_budget, budget_warnings, per_guest_cost
from .checklist import build_vendor_checklist
from .models import EventInput, Plan
from .timeline import build_timeline


def create_plan(event: EventInput, generator: TextGenerator | None = None, today: date | None = None) -> Plan:
    """Build the plan. Local parts are instant; only ideas may call Gemini (once)."""
    budget = allocate_budget(event.event_type, event.budget_inr)
    timeline = build_timeline(event.event_type, event.event_date, today)
    warnings = budget_warnings(event.event_type, event.budget_inr, event.guests)
    overdue = sum(item.overdue for item in timeline)
    if overdue:
        warnings.append(f"{overdue} task(s) are already past their ideal date — they are moved to today.")
    return Plan(
        event=event,
        budget=budget,
        per_guest_inr=per_guest_cost(event.budget_inr, event.guests),
        timeline=timeline,
        vendors=build_vendor_checklist(budget),
        ideas=generate_ideas(event, generator),
        warnings=warnings,
    )
