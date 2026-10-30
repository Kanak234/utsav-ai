"""Downloads: Markdown, PDF and calendar (.ics).

Why three formats: Markdown is easy to paste into WhatsApp/Notes, PDF is easy
to print or share with family, and .ics drops every timeline task into Google
Calendar / Outlook as a reminder — the timeline becomes actionable.
Flow: app.py "Export" tab -> to_markdown / to_pdf / to_ics -> st.download_button
"""

from __future__ import annotations

from datetime import datetime, timezone

from .budget import format_inr
from .models import Plan

APP_URL = "https://utsav-ai.streamlit.app"


def _rupees(amount: int) -> str:
    return f"Rs. {format_inr(amount)}"


def to_markdown(plan: Plan) -> str:
    """Human-readable plan; also the single source the PDF is drawn from."""
    ev, ideas = plan.event, plan.ideas
    lines = [
        f"# {ev.event_name}",
        f"{ev.event_type.value} · {ev.city} · {ev.event_date:%d %b %Y} · {ev.guests} guests · {_rupees(ev.budget_inr)}",
        "",
        "## Budget",
        *(f"- {b.category}: {_rupees(b.amount_inr)} ({b.percent:.0f}%)" for b in plan.budget),
        f"- Per guest: {_rupees(plan.per_guest_inr)}",
        "",
        "## Timeline",
        *(f"- [ ] {t.due:%d %b %Y} — {t.task}{' (overdue)' if t.overdue else ''}" for t in plan.timeline),
        "",
        "## Vendor checklist",
    ]
    for vendor in plan.vendors:
        lines.append(f"- [ ] {vendor.vendor} (budget {_rupees(vendor.budget_inr)})")
        lines.extend(f"    - {q}" for q in vendor.questions)
    sections = (
        ("Decor", ideas.decor),
        ("Food", ideas.food),
        ("Activities", ideas.activities),
        ("Money-saving tips", ideas.money_saving_tips),
    )
    lines += ["", "## Personalised ideas", ideas.theme_concept]
    for title, items in sections:
        lines += ["", f"### {title}", *(f"- {item}" for item in items)]
    if plan.warnings:
        lines += ["", "## Notes", *(f"- {w}" for w in plan.warnings)]
    lines += ["", f"_Made with Utsav AI by Kanak Prabhakar — {APP_URL}_"]
    return "\n".join(lines)


def _latin1(text: str) -> str:
    """PDF core fonts are Latin-1 only; swap common symbols and drop the rest safely."""
    swaps = {"₹": "Rs.", "—": "-", "–": "-", "·": "|", "’": "'", "“": '"', "”": '"', "…": "..."}
    for old, new in swaps.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def to_pdf(plan: Plan) -> bytes:
    """Render the Markdown plan into a simple, printable A4 PDF."""
    from fpdf import FPDF  # lazy import: only loaded when someone actually downloads

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    for raw in to_markdown(plan).splitlines():
        line = _latin1(raw)
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 18)
            text = line[2:]
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            text = line[3:]
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 12)
            text = line[4:]
        else:
            pdf.set_font("Helvetica", "", 10)
            text = line.replace("- [ ]", "[  ]").strip("_")
        pdf.multi_cell(0, 6, text or " ", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def _ics_escape(text: str) -> str:
    """Escape characters that have meaning in the iCalendar format (RFC 5545)."""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def to_ics(plan: Plan) -> str:
    """One all-day calendar event per timeline task."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Utsav AI//Event Planner//EN", "CALSCALE:GREGORIAN"]
    for index, item in enumerate(plan.timeline):
        out += [
            "BEGIN:VEVENT",
            f"UID:utsav-{plan.event.event_date:%Y%m%d}-{index}@utsav-ai",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{item.due:%Y%m%d}",
            f"SUMMARY:{_ics_escape(f'{plan.event.event_name}: {item.task}')}",
            "END:VEVENT",
        ]
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"  # RFC 5545 requires CRLF line endings
