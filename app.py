"""Utsav AI — Streamlit user interface.

This file only does UI. All planning logic lives in the `utsav` package so it
can be tested without a browser.
Flow: sidebar form -> validation.build_event_input -> cached Gemini ideas -> planner.create_plan
      -> tabs (Overview, Budget, Timeline, Vendors, Ideas, Export)
"""

from __future__ import annotations

import base64
import os
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from utsav.ai import GeminiGenerator, TextGenerator, generate_ideas, offline_ideas
from utsav.budget import format_inr
from utsav.constants import DEFAULT_MODELS
from utsav.export import to_ics, to_markdown, to_pdf
from utsav.models import EventInput, EventType, Ideas, Plan
from utsav.planner import create_plan
from utsav.timeline import days_left
from utsav.validation import build_event_input

ASSETS = Path(__file__).parent / "assets"
PRIVACY_URL = "https://kanak234.github.io/utsav-ai/privacy.html"
TERMS_URL = "https://kanak234.github.io/utsav-ai/terms.html"

# Must be the first Streamlit call. Sets tab title + favicon (SEO / polish).
st.set_page_config(page_title="Utsav AI — Event Planner", page_icon="🪔", layout="wide")


# ---------- Cached resources (efficiency) ------------------------------------
def _secret(name: str) -> str:
    """Read a secret from Streamlit secrets or env vars; never hard-coded, never sent to the browser."""
    try:
        value = st.secrets.get(name, "")
    except Exception:  # no secrets.toml locally -> fall back to environment
        value = ""
    return str(value or os.environ.get(name, ""))


@st.cache_resource(show_spinner=False)
def get_generator() -> TextGenerator | None:
    """Create the Gemini client ONCE per server process, not on every rerun."""
    key = _secret("GEMINI_API_KEY")
    if not key:
        return None
    model = _secret("GEMINI_MODEL")
    return GeminiGenerator(key, (model, *DEFAULT_MODELS) if model else DEFAULT_MODELS)


class AIUnavailableError(RuntimeError):
    """Raised inside the cached function so a failed AI call is NOT cached."""


@st.cache_data(show_spinner=False, ttl=3600, max_entries=128)
def gemini_ideas(event: EventInput, _generator: TextGenerator) -> Ideas:
    """Same event -> reuse Gemini's answer for an hour instead of calling it again.

    Streamlit never caches a function that raises, so only SUCCESSFUL answers are
    stored; after a temporary Gemini outage the next request tries again.
    `_generator` starts with "_" so Streamlit doesn't try to hash the client.
    """
    ideas = generate_ideas(event, _generator)
    if ideas.source != "gemini":
        raise AIUnavailableError
    return ideas


def get_ideas(event: EventInput, generator: TextGenerator | None) -> Ideas:
    """Gemini ideas when possible, otherwise offline ideas with a plain-language reason."""
    if generator is None:
        return replace(offline_ideas(event), note="Offline ideas — no Gemini API key is configured on the server.")
    try:
        return gemini_ideas(event, generator)
    except AIUnavailableError:
        return replace(
            offline_ideas(event), note="Offline ideas — Gemini didn't respond. Press Create my plan to retry."
        )


@st.cache_data(show_spinner=False)
def logo_data_uri() -> str:
    """Inline the KP watermark as a data URI (one less network request)."""
    data = (ASSETS / "logo-mark.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode()


# ---------- UI pieces ----------------------------------------------------------
def render_header() -> None:
    st.title("🪔 Utsav AI")
    st.markdown(
        "**Plan weddings, birthdays and community events** — a budget that adds up, a dated timeline, "
        "a vendor checklist and personalised ideas, in one place."
    )


def render_form() -> EventInput | None:
    """Sidebar form. Returns a validated EventInput once the user submits valid data."""
    with st.sidebar:
        st.header("Tell us about your event")
        with st.form("event_form", border=False):
            event_type = st.selectbox("Event type", [e.value for e in EventType], help="Choose the kind of event.")
            event_name = st.text_input("Event name", value="Riya & Aman's Wedding", max_chars=80)
            city = st.text_input("City / town", value="Hazaribagh", max_chars=60)
            event_date = st.date_input(
                "Event date", value=date.today() + timedelta(days=90), min_value=date.today(), format="DD/MM/YYYY"
            )
            guests = st.number_input("Number of guests", min_value=1, max_value=10_000, value=300, step=10)
            budget = st.number_input(
                "Total budget (₹)", min_value=1_000, max_value=100_000_000, value=800_000, step=10_000
            )
            theme = st.text_input("Theme or vibe (optional)", placeholder="e.g. royal Rajasthani, pastel, eco-friendly")
            preferences = st.text_area(
                "Preferences (optional)", placeholder="e.g. pure veg, no alcohol, elderly guests", max_chars=300
            )
            submitted = st.form_submit_button("✨ Create my plan", type="primary", use_container_width=True)

    if submitted:
        event, errors = build_event_input(
            event_type=event_type,
            event_name=event_name,
            city=city,
            event_date=event_date,
            guests=int(guests),
            budget_inr=int(budget),
            theme=theme,
            preferences=preferences,
        )
        for message in errors:
            st.sidebar.error(message, icon="⚠️")
        if event:
            st.session_state["event"] = event
    return st.session_state.get("event")


def render_overview(plan: Plan) -> None:
    ev = plan.event
    cols = st.columns(4)
    cols[0].metric("Days to go", days_left(ev.event_date))
    cols[1].metric("Guests", f"{ev.guests:,}")
    cols[2].metric("Budget", f"₹{format_inr(ev.budget_inr)}")
    cols[3].metric("Per guest", f"₹{format_inr(plan.per_guest_inr)}")
    for warning in plan.warnings:
        st.warning(warning, icon="⚠️")
    st.subheader("Next 3 tasks")
    for item in plan.timeline[:3]:
        st.markdown(f"- **{item.due:%d %b %Y}** — {item.task}{' · *overdue*' if item.overdue else ''}")


def render_budget(plan: Plan) -> None:
    st.subheader("Budget split")
    rows = {b.category: b.amount_inr for b in plan.budget}
    st.bar_chart(rows, horizontal=True, x_label="Category", y_label="Amount (₹)")
    # The table repeats the chart's data in text so it's readable by screen readers (accessibility).
    st.table(
        {
            "Category": list(rows),
            "Amount (₹)": [format_inr(v) for v in rows.values()],
            "Share": [f"{b.percent:.0f}%" for b in plan.budget],
        }
    )


def _progress_checkbox(label: str, key: str) -> bool:
    """Checkbox whose tick survives reruns via session_state."""
    return st.checkbox(label, key=key)


def render_timeline(plan: Plan) -> None:
    st.subheader("Countdown timeline")
    done = sum(
        _progress_checkbox(
            f"{item.due:%d %b %Y} — {item.task}" + (" (overdue — do now)" if item.overdue else ""), f"t{i}"
        )
        for i, item in enumerate(plan.timeline)
    )
    st.progress(done / len(plan.timeline), text=f"{done} of {len(plan.timeline)} tasks done")


def render_vendors(plan: Plan) -> None:
    st.subheader("Vendor checklist")
    for i, vendor in enumerate(plan.vendors):
        _progress_checkbox(f"**{vendor.vendor}** booked — budget ₹{format_inr(vendor.budget_inr)}", f"v{i}")
        with st.expander(f"Questions to ask: {vendor.vendor}"):
            st.markdown("\n".join(f"- {q}" for q in vendor.questions))


def render_ideas(plan: Plan) -> None:
    ideas = plan.ideas
    label = "✨ Generated by Google Gemini" if ideas.source == "gemini" else ideas.note or "Offline ideas"
    st.caption(label)
    st.info(ideas.theme_concept, icon="💡")
    cols = st.columns(2)
    blocks = (
        ("🎨 Decor", ideas.decor),
        ("🍛 Food", ideas.food),
        ("🎉 Activities", ideas.activities),
        ("💰 Money-saving tips", ideas.money_saving_tips),
    )
    for index, (title, items) in enumerate(blocks):
        with cols[index % 2]:
            st.markdown(f"#### {title}")
            st.markdown("\n".join(f"- {item}" for item in items) or "_No ideas_")


def render_export(plan: Plan) -> None:
    st.subheader("Take your plan with you")
    slug = "".join(ch if ch.isalnum() else "-" for ch in plan.event.event_name.lower()).strip("-") or "plan"
    cols = st.columns(3)
    cols[0].download_button("⬇️ PDF", to_pdf(plan), f"{slug}.pdf", "application/pdf", use_container_width=True)
    cols[1].download_button("⬇️ Markdown", to_markdown(plan), f"{slug}.md", "text/markdown", use_container_width=True)
    cols[2].download_button(
        "📅 Calendar (.ics)", to_ics(plan), f"{slug}.ics", "text/calendar", use_container_width=True
    )


def render_footer() -> None:
    st.divider()
    st.markdown(
        f'<img src="{logo_data_uri()}" alt="KP logo — Kanak Prabhakar" width="28" style="vertical-align:middle"> '
        f"Built by <b>Kanak Prabhakar</b> · <a href='{PRIVACY_URL}'>Privacy</a> · <a href='{TERMS_URL}'>Terms</a> · "
        "No account, no cookies: your event details are used only to make this plan.",
        unsafe_allow_html=True,  # safe: only our own constant HTML, never user text
    )


def main() -> None:
    render_header()
    event = render_form()
    if event is None:
        st.info("👈 Fill in your event details and press **Create my plan**.", icon="🪔")
        render_footer()
        return
    with st.spinner("Planning your celebration…"):
        plan = create_plan(event, today=date.today(), ideas=get_ideas(event, get_generator()))
    tabs = st.tabs(["Overview", "Budget", "Timeline", "Vendors", "Ideas", "Export"])
    renderers = (render_overview, render_budget, render_timeline, render_vendors, render_ideas, render_export)
    for tab, render in zip(tabs, renderers, strict=True):
        with tab:
            render(plan)
    render_footer()


main()
