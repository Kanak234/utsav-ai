<div align="center">

<img src="docs/icons/icon-192.png" alt="Utsav AI diya logo" width="96">

# Utsav AI

**GenAI planning assistant for weddings, birthdays and community events.**
Budget that adds up · dated timeline · vendor checklist · personalised ideas — in one screen.

[![CI](https://github.com/Kanak234/utsav-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Kanak234/utsav-ai/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

[**▶ Live app**](https://utsav-ai.streamlit.app) · [Windows app (Microsoft Store)](STORE_GUIDE.md) · [Privacy](https://kanak234.github.io/utsav-ai/privacy.html)

</div>

---

## The problem

Planning an Indian celebration means juggling a budget, dozens of deadlines and many vendors — usually in a notebook or a WhatsApp group. Generic chatbots give ideas but their numbers don't add up and nothing turns into an actionable plan.

## What Utsav AI does — mapped to the challenge brief

| Challenge asks for | How Utsav AI delivers it | Code |
|---|---|---|
| **Weddings, birthdays, community events** | Separate rules for each type (budget split, tasks, vendors) | `utsav/constants.py` |
| **Budgets** | Category split that sums **exactly** to your total, per-guest cost, tight-budget warning, chart + table | `utsav/budget.py` |
| **Timelines** | Countdown with real dates; tasks you're late for move to "today" instead of vanishing; export to Google Calendar/Outlook (.ics) | `utsav/timeline.py`, `utsav/export.py` |
| **Vendor checklists** | One vendor per category with its budget cap and questions to ask before paying an advance; tick-off progress | `utsav/checklist.py` |
| **Personalised ideas (GenAI)** | Google **Gemini** generates theme, decor, food, activities and money-saving tips for *your* city, budget and preferences | `utsav/ai.py`, `utsav/prompts.py` |
| Take it offline | PDF, Markdown and calendar downloads | `utsav/export.py` |

## Why it's built this way

- **AI only where creativity helps.** Money and dates are computed with plain maths (always correct); Gemini writes the ideas. One small JSON call per plan.
- **Never breaks.** No API key, quota exhausted or bad AI output → clean rule-based ideas are shown and the label says so.
- **Fast.** Gemini client is created once (`st.cache_resource`), identical plans are cached for an hour (`st.cache_data`), heavy libraries load lazily, and only three runtime dependencies.
- **Secure.** Inputs are normalised, HTML/control characters stripped, prompt-injection phrases neutralised, user text fenced as *data* in the prompt, model output re-validated, API key only in Streamlit secrets, XSRF protection on, no user HTML rendered.
- **Accessible.** Every input labelled, every chart duplicated as a table, no meaning by colour alone, WCAG-AA contrast (≥ 5.3 : 1), keyboard-friendly form, skip link and alt text on the web shell.

```
app.py (UI only)
  └─ validation.build_event_input ──► planner.create_plan
                                        ├─ budget     (maths)
                                        ├─ timeline   (dates)
                                        ├─ checklist  (vendors)
                                        └─ ai ──► Gemini (1 call, JSON) ─► fallback if needed
                                     export ─► PDF · Markdown · .ics
```

## Run locally

```bash
git clone https://github.com/Kanak234/utsav-ai && cd utsav-ai && pip install -r requirements-dev.txt && streamlit run app.py
```
Add your free key from [Google AI Studio](https://aistudio.google.com/apikey) to `.streamlit/secrets.toml` (see `secrets.toml.example`). Without a key the app still works with offline ideas.

## Tests & quality

```bash
ruff check . && ruff format --check . && pytest
```
48 tests cover validation & injection cleaning, exact budget sums for every event type, timeline compression, vendor checklists, Gemini JSON parsing/fallback (with a fake model — no network), all three exporters, and an end-to-end UI run with Streamlit `AppTest`. CI runs them on every push.

## Project docs

[PRD](project-docs/PRD.md) · [TRD](project-docs/TRD.md) · [UI/UX brief](project-docs/DESIGN.md) · [Microsoft Store guide](STORE_GUIDE.md)

## Author

Built by **Kanak Prabhakar** — BCA (Cyber Security), AISECT University · [GitHub](https://github.com/Kanak234) · YouTube: *Cooding with Kanak*

MIT License
