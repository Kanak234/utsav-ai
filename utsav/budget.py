"""Budget allocation — deterministic maths, no AI.

Why no AI here: money must add up exactly every time. An LLM can produce
numbers that don't sum to the total; plain arithmetic can't. Gemini is used
only for the creative parts (ai.py), where variety is a feature.
Flow: planner.py -> allocate_budget() -> list[BudgetLine] -> app.py chart + export.py
"""

from __future__ import annotations

from .constants import BUDGET_SPLIT, LOW_PER_GUEST_INR
from .models import BudgetLine, EventType


def format_inr(amount: int) -> str:
    """Indian digit grouping: 1234567 -> '12,34,567' (lakh/crore style users expect)."""
    sign, digits = ("-" if amount < 0 else ""), str(abs(int(amount)))
    if len(digits) <= 3:
        return sign + digits
    head, tail = digits[:-3], digits[-3:]
    # Group the remaining digits in pairs from the right: 12,34 + ,567
    pairs = [head[max(i - 2, 0) : i] for i in range(len(head), 0, -2)][::-1]
    return sign + ",".join(pairs) + "," + tail


def allocate_budget(event_type: EventType, total_inr: int) -> list[BudgetLine]:
    """Split `total_inr` across categories so the parts sum EXACTLY to the total.

    Integer flooring loses a few rupees; the remainder goes to the largest
    category so nothing "disappears" (largest-remainder rounding, O(n)).
    """
    split = BUDGET_SPLIT[event_type]
    amounts = {cat: total_inr * pct // 100 for cat, pct in split.items()}
    remainder = total_inr - sum(amounts.values())
    if remainder:
        biggest = max(split, key=split.__getitem__)
        amounts[biggest] += remainder
    return [BudgetLine(cat, amounts[cat], float(pct)) for cat, pct in split.items()]


def per_guest_cost(total_inr: int, guests: int) -> int:
    """Average spend per guest, rounded down (guests is validated >= 1)."""
    return total_inr // max(guests, 1)


def budget_warnings(event_type: EventType, total_inr: int, guests: int) -> list[str]:
    """Plain-language warnings when the budget looks too tight for the headcount."""
    per_guest = per_guest_cost(total_inr, guests)
    floor = LOW_PER_GUEST_INR[event_type]
    if per_guest < floor:
        return [
            f"Budget is tight: about ₹{format_inr(per_guest)} per guest (typical minimum ≈ ₹{format_inr(floor)}). "
            "Consider fewer guests, a community hall, or a potluck-style menu."
        ]
    return []
