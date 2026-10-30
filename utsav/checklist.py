"""Vendor checklist builder.

Why: the problem statement asks for vendor checklists. Each budget category
(except the buffer) becomes a vendor to book, carrying its own budget cap and
the questions worth asking before paying an advance.
Flow: planner.py -> build_vendor_checklist(budget lines) -> list[VendorItem] -> app.py checkboxes + export.py
"""

from __future__ import annotations

from collections.abc import Iterable

from .constants import COMMON_VENDOR_QUESTIONS, CONTINGENCY, VENDOR_SPECIFIC_QUESTIONS
from .models import BudgetLine, VendorItem


def _questions_for(category: str) -> tuple[str, ...]:
    """Common questions + any keyword-matched specific ones (no duplicates, order kept)."""
    lowered = category.lower()
    specific = [q for key, qs in VENDOR_SPECIFIC_QUESTIONS.items() if key in lowered for q in qs]
    # dict.fromkeys removes duplicates while keeping order (two keywords can share a question).
    return tuple(dict.fromkeys([*specific, *COMMON_VENDOR_QUESTIONS]))


def build_vendor_checklist(budget: Iterable[BudgetLine]) -> list[VendorItem]:
    """One VendorItem per real spending category; the contingency buffer is not a vendor."""
    return [
        VendorItem(vendor=line.category, budget_inr=line.amount_inr, questions=_questions_for(line.category))
        for line in budget
        if line.category != CONTINGENCY
    ]
