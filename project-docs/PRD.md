# PRD — Utsav AI

## Overview
A GenAI planning assistant (PromptWars Virtual, Challenge 05) that helps users organise weddings, birthdays and community events with budgets, timelines, vendor checklists and personalised ideas.

## Problem
Event planning in India is spread across notebooks, calls and WhatsApp. Chatbots give ideas but not a plan whose numbers add up.

## Users
- Families planning a wedding (large budget, 6-month lead time)
- Parents planning a birthday (small budget, 2–4 weeks)
- Committees planning a puja / mela / society event (permits, volunteers, sponsors)

## Goals / Non-goals
- Goals: one-screen plan in < 10 s; budget always sums exactly; works even if AI fails; exportable.
- Non-goals: vendor marketplace, payments, user accounts, storing personal data.

## Features & exact behaviour
1. Form: type, name, city, date (today … +2 yrs), guests (1–10,000), budget (₹1,000–₹10 cr), theme, preferences (≤300 chars).
2. Budget: per-type % split, integer amounts summing exactly to total; per-guest cost; warning below per-type floor.
3. Timeline: fixed milestones converted to dates; past-due milestones moved to today and flagged; progress bar.
4. Vendor checklist: one item per non-buffer category, with budget cap and ≥3 questions.
5. Ideas: one Gemini call returning JSON (theme, decor, food, activities, tips ≤5 each); offline fallback on any failure; source label shown.
6. Export: PDF, Markdown, .ics.

## Edge cases
Empty/whitespace name; past date; 0 or 20,000 guests; budget below minimum; HTML / prompt-injection text; event in 2 days (all tasks overdue); Gemini timeout/quota/garbage JSON; no API key; non-Latin text in PDF.

## Acceptance criteria
All of the above covered by automated tests (`pytest`, 48 tests), lint clean, app deploys on Streamlit Cloud, Store package passes PWABuilder checks.
