"""Tests for budget, timeline, checklist and the planner pipeline."""

from __future__ import annotations

from datetime import timedelta

import pytest

from utsav.budget import allocate_budget, budget_warnings, per_guest_cost
from utsav.checklist import build_vendor_checklist
from utsav.constants import BUDGET_SPLIT, CONTINGENCY
from utsav.models import EventType
from utsav.planner import create_plan
from utsav.timeline import build_timeline, days_left


@pytest.mark.parametrize("kind", list(EventType))
def test_every_split_sums_to_100(kind):
    assert sum(BUDGET_SPLIT[kind].values()) == 100


@pytest.mark.parametrize("total", [1_000, 99_999, 800_000, 1_234_567])
@pytest.mark.parametrize("kind", list(EventType))
def test_budget_adds_up_exactly(kind, total):
    lines = allocate_budget(kind, total)
    assert sum(line.amount_inr for line in lines) == total
    assert all(line.amount_inr >= 0 for line in lines)


def test_per_guest_and_tight_budget_warning():
    assert per_guest_cost(10_000, 100) == 100
    assert budget_warnings(EventType.WEDDING, 10_000, 100)
    assert budget_warnings(EventType.WEDDING, 1_000_000, 100) == []


def test_timeline_dates_are_relative_to_event(today):
    event_day = today + timedelta(days=200)
    items = build_timeline(EventType.WEDDING, event_day, today)
    assert items[-1].due == event_day
    assert [i.due for i in items] == sorted(i.due for i in items)
    assert not any(i.overdue for i in items)


def test_short_notice_tasks_move_to_today(today):
    items = build_timeline(EventType.WEDDING, today + timedelta(days=10), today)
    overdue = [i for i in items if i.overdue]
    assert overdue and all(i.due == today for i in overdue)
    assert days_left(today + timedelta(days=10), today) == 10


def test_vendor_checklist_skips_contingency_and_has_questions():
    vendors = build_vendor_checklist(allocate_budget(EventType.COMMUNITY, 200_000))
    assert CONTINGENCY not in {v.vendor for v in vendors}
    assert all(len(v.questions) >= 3 for v in vendors)
    assert all(len(v.questions) == len(set(v.questions)) for v in vendors)


def test_create_plan_offline(wedding, today):
    plan = create_plan(wedding, None, today)
    assert sum(b.amount_inr for b in plan.budget) == wedding.budget_inr
    assert plan.ideas.source == "offline"
    assert plan.vendors and plan.timeline


def test_create_plan_flags_overdue(wedding, today):
    from dataclasses import replace

    plan = create_plan(replace(wedding, event_date=today + timedelta(days=5)), None, today)
    assert any("moved to today" in w for w in plan.warnings)


@pytest.mark.parametrize(
    ("amount", "expected"),
    [(0, "0"), (999, "999"), (1_000, "1,000"), (200_000, "2,00,000"), (12_345_678, "1,23,45,678"), (-1500, "-1,500")],
)
def test_format_inr_uses_indian_grouping(amount, expected):
    from utsav.budget import format_inr

    assert format_inr(amount) == expected


def test_create_plan_reuses_given_ideas(wedding, today, fake_generator_cls):
    from utsav.ai import offline_ideas

    fake = fake_generator_cls(reply="{}")
    ideas = offline_ideas(wedding)
    plan = create_plan(wedding, fake, today, ideas=ideas)
    assert plan.ideas is ideas and fake.prompts == []  # no AI call when ideas are supplied
