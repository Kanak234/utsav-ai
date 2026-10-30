"""Shared pytest fixtures.

A fixed `TODAY` makes every date-based test deterministic (it never depends
on the day the tests are run). Flow: imported automatically by pytest.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

# Make `import utsav` work when pytest is run from the repo root without installing.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utsav.models import EventInput, EventType  # noqa: E402

TODAY = date(2026, 11, 1)


@pytest.fixture
def today() -> date:
    return TODAY


@pytest.fixture
def wedding(today: date) -> EventInput:
    return EventInput(
        event_type=EventType.WEDDING,
        event_name="Riya & Aman",
        city="Hazaribagh",
        event_date=today + timedelta(days=200),
        guests=300,
        budget_inr=800_000,
        theme="royal",
        preferences="pure veg",
    )


class FakeGenerator:
    """Stands in for Gemini: returns canned text or raises, and records prompts."""

    def __init__(self, reply: str = "", error: Exception | None = None) -> None:
        self.reply, self.error, self.prompts = reply, error, []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.reply


@pytest.fixture
def fake_generator_cls() -> type[FakeGenerator]:
    return FakeGenerator
