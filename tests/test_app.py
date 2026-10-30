"""End-to-end UI smoke test using Streamlit's built-in AppTest (no browser needed)."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_app_starts_with_prompt(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert "Create my plan" in at.info[0].value


def test_submit_builds_full_plan(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.button[0].click().run()
    assert not at.exception
    assert len(at.tabs) == 6
    assert any("Days to go" in m.label for m in at.metric)


def test_invalid_input_shows_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.text_input[0].set_value("   ")
    at.sidebar.button[0].click().run()
    assert any("name" in e.value for e in at.sidebar.error)


def test_no_key_explains_offline_ideas(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.button[0].click().run()
    assert any("no Gemini API key" in c.value for c in at.caption)
