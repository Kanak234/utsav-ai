"""All tunable values in one place.

Why: keeping percentages, limits and task lists here (instead of scattered
inside functions) means the planning rules can be reviewed or changed without
touching any logic. Flow: read by validation.py, budget.py, timeline.py, checklist.py, ai.py.
"""

from __future__ import annotations

from types import MappingProxyType

from .models import EventType

# ---- Input limits (validation.py) -------------------------------------------
# Upper bounds stop absurd values and keep the AI prompt small (efficiency + security).
MIN_GUESTS = 1
MAX_GUESTS = 10_000
MIN_BUDGET_INR = 1_000
MAX_BUDGET_INR = 100_000_000  # ₹10 crore
MAX_TEXT_LEN = 300  # free-text fields are capped before they reach the prompt
MAX_PLANNING_DAYS = 730  # events more than 2 years away are rejected

# ---- Budget split (budget.py) -------------------------------------------------
# Percent of total budget per category. Each mapping sums to exactly 100.
# MappingProxyType makes them read-only so no code can mutate shared rules.
CONTINGENCY = "Contingency (buffer)"

BUDGET_SPLIT = MappingProxyType(
    {
        EventType.WEDDING: MappingProxyType(
            {
                "Venue": 25,
                "Catering": 30,
                "Decor & Flowers": 10,
                "Photography & Video": 8,
                "Attire & Jewellery": 10,
                "Music & Entertainment": 5,
                "Invitations & Gifts": 2,
                CONTINGENCY: 10,
            }
        ),
        EventType.BIRTHDAY: MappingProxyType(
            {
                "Venue": 20,
                "Food & Cake": 35,
                "Decor & Balloons": 15,
                "Entertainment & Games": 12,
                "Return Gifts": 8,
                CONTINGENCY: 10,
            }
        ),
        EventType.COMMUNITY: MappingProxyType(
            {
                "Venue & Permits": 20,
                "Food & Prasad": 25,
                "Tent, Stage & Sound": 20,
                "Decor & Lighting": 10,
                "Volunteers & Logistics": 8,
                "Publicity & Printing": 7,
                CONTINGENCY: 10,
            }
        ),
    }
)

# Below this per-guest spend the plan warns the user that the budget is tight.
LOW_PER_GUEST_INR = MappingProxyType({EventType.WEDDING: 800, EventType.BIRTHDAY: 300, EventType.COMMUNITY: 150})

# ---- Timeline (timeline.py) ---------------------------------------------------
# (days before the event, task). Sorted far-to-near. Tasks whose ideal date has
# already passed are compressed to "do now" and flagged instead of being dropped.
TIMELINE_TASKS = MappingProxyType(
    {
        EventType.WEDDING: (
            (180, "Fix the date with both families and set the total budget"),
            (150, "Shortlist and book the venue"),
            (120, "Book caterer, photographer and decorator"),
            (90, "Finalise guest list and send save-the-dates"),
            (60, "Order attire and jewellery; book mehendi artist"),
            (45, "Send invitations; book transport and guest stay"),
            (30, "Menu tasting and decor sign-off"),
            (14, "Confirm RSVPs and share final headcount with caterer"),
            (7, "Pay pending advances; share run-sheet with all vendors"),
            (2, "Final venue walkthrough and trial of sound/lighting"),
            (0, "Wedding day — follow the run-sheet, keep the buffer ready"),
        ),
        EventType.BIRTHDAY: (
            (30, "Pick the theme, venue and guest list"),
            (21, "Book venue, cake and entertainment"),
            (14, "Send invitations (WhatsApp / cards)"),
            (7, "Order decor and return gifts; confirm RSVPs"),
            (3, "Confirm cake design and food count"),
            (1, "Set up decor and charge camera / speakers"),
            (0, "Party day — cake cutting, games, photos"),
        ),
        EventType.COMMUNITY: (
            (60, "Form the organising committee and assign roles"),
            (45, "Apply for venue, police and municipal permissions"),
            (30, "Book tent, stage, sound and caterer; start publicity"),
            (21, "Recruit volunteers and plan crowd flow / first aid"),
            (14, "Print banners and posters; confirm sponsors"),
            (7, "Volunteer briefing; confirm all vendors"),
            (2, "Venue setup, sound check, safety check"),
            (0, "Event day — registration desk, schedule, clean-up crew"),
        ),
    }
)

# ---- Vendor questions (checklist.py) -----------------------------------------
# Shared questions apply to every vendor; specific ones are matched by keyword.
COMMON_VENDOR_QUESTIONS = (
    "What exactly is included in the quoted price?",
    "How much advance is needed and what is the cancellation policy?",
    "Can you share a written quote / invoice with GST?",
)

VENDOR_SPECIFIC_QUESTIONS = MappingProxyType(
    {
        "venue": ("Is power backup and parking included?", "What are the access hours on the day?"),
        "catering": ("Is a tasting session free?", "Do you handle veg / Jain / allergy-safe dishes?"),
        "food": ("Is a tasting session free?", "Can you handle dietary restrictions?"),
        "decor": ("Can we see photos of a setup at this venue size?", "Who removes the decor after?"),
        "photography": ("How many edited photos and when are they delivered?", "Is a drone shot included?"),
        "music": ("How long is the set and are breaks included?", "Who provides the sound system?"),
        "tent": ("Is the structure weather-safe?", "Do you provide fire extinguishers?"),
        "entertainment": ("Are activities age-appropriate?", "How much space do you need?"),
    }
)

# ---- AI (ai.py) --------------------------------------------------------------
# Model is configurable through Streamlit secrets; these are tried in order.
DEFAULT_MODELS = ("gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest")
AI_TIMEOUT_MS = 20_000
AI_MAX_OUTPUT_TOKENS = 900  # ideas are short lists — a small cap keeps calls fast
AI_TEMPERATURE = 0.8
MAX_IDEAS_PER_LIST = 5
