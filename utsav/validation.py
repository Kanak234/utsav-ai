"""Input cleaning and validation — the app's first line of defence.

Why: every value typed by the user eventually reaches either the maths
(budget/timeline) or the Gemini prompt. Cleaning it once, here, means:
  * no control characters / HTML tags are echoed back into the page (XSS-safe),
  * free text is length-capped (keeps the prompt small and fast),
  * obvious prompt-injection phrases are neutralised before reaching the model,
  * bad numbers produce friendly messages instead of crashes.
Flow: app.py form -> build_event_input() -> EventInput (or a list of errors) -> planner.py
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

from .constants import (
    MAX_BUDGET_INR,
    MAX_GUESTS,
    MAX_PLANNING_DAYS,
    MAX_TEXT_LEN,
    MIN_BUDGET_INR,
    MIN_GUESTS,
)
from .models import EventInput, EventType

# Compiled once at import time so repeated validation is cheap (efficiency).
_TAG_RE = re.compile(r"<[^>]*>")
_SPACE_RE = re.compile(r"\s+")
# Phrases commonly used to hijack an LLM. We don't block the user — we just
# strip the phrase so it can't act as an instruction inside our prompt.
_INJECTION_RE = re.compile(
    r"(ignore|disregard|forget)\s+(all\s+|any\s+)?(previous|prior|above)\s+(instructions|prompts?)"
    r"|system\s*prompt|you\s+are\s+now",
    re.IGNORECASE,
)


def clean_text(value: str | None, max_len: int = MAX_TEXT_LEN) -> str:
    """Return a safe, single-line, length-capped version of free text.

    Steps: normalise unicode -> drop control chars -> drop HTML tags ->
    neutralise injection phrases -> collapse whitespace -> cap length.
    """
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    # Category "C*" = control/format chars (e.g. \x00, zero-width joiners used to hide text).
    text = "".join(ch for ch in text if not unicodedata.category(ch).startswith("C") or ch == " ")
    text = _TAG_RE.sub("", text)
    text = _INJECTION_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text[:max_len]


def _parse_event_type(raw: str) -> EventType | None:
    """Map the UI label back to the enum; None if it isn't one we support."""
    try:
        return EventType(raw)
    except ValueError:
        return None


def build_event_input(
    *,
    event_type: str,
    event_name: str,
    city: str,
    event_date: date,
    guests: int,
    budget_inr: int,
    theme: str = "",
    preferences: str = "",
    today: date | None = None,
) -> tuple[EventInput | None, list[str]]:
    """Validate raw form values.

    Returns (EventInput, []) on success or (None, [error messages]) on failure,
    so the UI can show every problem at once instead of one at a time.
    `today` is injectable so tests are deterministic.
    """
    today = today or date.today()
    errors: list[str] = []

    kind = _parse_event_type(event_type)
    if kind is None:
        errors.append("Please choose Wedding, Birthday or Community Event.")

    name = clean_text(event_name, 80)
    if not name:
        errors.append("Please give your event a name.")

    place = clean_text(city, 60)
    if not place:
        errors.append("Please enter the city or town.")

    if not isinstance(guests, int) or not MIN_GUESTS <= guests <= MAX_GUESTS:
        errors.append(f"Guests must be between {MIN_GUESTS} and {MAX_GUESTS:,}.")

    if not isinstance(budget_inr, int) or not MIN_BUDGET_INR <= budget_inr <= MAX_BUDGET_INR:
        errors.append(f"Budget must be between ₹{MIN_BUDGET_INR:,} and ₹{MAX_BUDGET_INR:,}.")

    if not isinstance(event_date, date):
        errors.append("Please pick a valid event date.")
    elif event_date < today:
        errors.append("The event date is in the past.")
    elif event_date > today + timedelta(days=MAX_PLANNING_DAYS):
        errors.append("Please pick a date within the next 2 years.")

    if errors or kind is None:
        return None, errors

    return (
        EventInput(
            event_type=kind,
            event_name=name,
            city=place,
            event_date=event_date,
            guests=guests,
            budget_inr=budget_inr,
            theme=clean_text(theme, 80),
            preferences=clean_text(preferences),
        ),
        [],
    )
