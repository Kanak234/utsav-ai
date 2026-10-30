"""Tests for Gemini parsing/fallback and the exporters (no network used)."""

from __future__ import annotations

import json

from utsav.ai import generate_ideas, parse_ideas
from utsav.export import to_ics, to_markdown, to_pdf
from utsav.planner import create_plan
from utsav.prompts import IDEA_KEYS, build_ideas_prompt

GOOD = json.dumps(
    {
        "theme_concept": "A royal marigold wedding",
        "decor": ["Marigold arch", "Diyas", "", 5, "<b>Lanterns</b>", "a", "b", "c"],
        "food": ["Litti chokha"],
        "activities": ["Sangeet"],
        "money_saving_tips": ["Weekday booking"],
    }
)


def test_parse_valid_json_cleans_and_caps():
    ideas = parse_ideas(GOOD)
    assert ideas is not None and ideas.source == "gemini"
    assert "Lanterns" in ideas.decor and all("<" not in d for d in ideas.decor)
    assert len(ideas.decor) == 5  # empty / non-string items dropped, then capped


def test_parse_handles_code_fences():
    assert parse_ideas(f"```json\n{GOOD}\n```") is not None


def test_parse_rejects_bad_output():
    assert parse_ideas("not json") is None
    assert parse_ideas(json.dumps({"decor": []})) is None
    assert parse_ideas(json.dumps({k: [] for k in IDEA_KEYS} | {"theme_concept": ""})) is None
    assert parse_ideas("[1, 2]") is None


def test_generate_ideas_uses_gemini_when_it_works(wedding, fake_generator_cls):
    fake = fake_generator_cls(reply=GOOD)
    assert generate_ideas(wedding, fake).source == "gemini"
    assert len(fake.prompts) == 1  # exactly one AI call per plan (efficiency)


def test_generate_ideas_falls_back_on_error_or_garbage(wedding, fake_generator_cls):
    assert generate_ideas(wedding, fake_generator_cls(error=TimeoutError())).source == "offline"
    assert generate_ideas(wedding, fake_generator_cls(reply="??")).source == "offline"
    assert generate_ideas(wedding, None).source == "offline"


def test_prompt_wraps_user_data_and_includes_details(wedding):
    prompt = build_ideas_prompt(wedding)
    assert "<event_details>" in prompt and "</event_details>" in prompt
    assert "Hazaribagh" in prompt and "800000" in prompt and "pure veg" in prompt


def test_exports(wedding, today):
    plan = create_plan(wedding, None, today)
    md = to_markdown(plan)
    assert md.startswith("# Riya & Aman") and "Vendor checklist" in md
    assert to_pdf(plan)[:5] == b"%PDF-"
    ics = to_ics(plan)
    assert ics.count("BEGIN:VEVENT") == len(plan.timeline)
    assert "\r\n" in ics and "Riya & Aman" in ics
