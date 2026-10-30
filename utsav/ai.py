"""Gemini integration with a safe offline fallback.

Design:
  * `TextGenerator` is a tiny Protocol — anything with `generate(prompt) -> str`.
    The real one is `GeminiGenerator`; tests pass a fake, so tests never hit the network.
  * The Gemini SDK is imported lazily inside GeminiGenerator, so app start-up
    and the offline path stay fast even if the SDK is slow to import.
  * Model output is treated as untrusted: parsed as JSON, keys checked, lists
    trimmed, strings cleaned. Anything wrong -> offline ideas, never a crash.
Flow: planner.py -> generate_ideas(event, generator) -> Ideas -> app.py "Ideas" tab
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

from .constants import (
    AI_MAX_OUTPUT_TOKENS,
    AI_TEMPERATURE,
    AI_TIMEOUT_MS,
    DEFAULT_MODELS,
    MAX_IDEAS_PER_LIST,
)
from .models import EventInput, EventType, Ideas
from .prompts import IDEA_KEYS, SYSTEM_INSTRUCTION, build_ideas_prompt
from .validation import clean_text

logger = logging.getLogger(__name__)


class TextGenerator(Protocol):
    """Anything that turns a prompt into text. Lets us swap Gemini for a fake in tests."""

    def generate(self, prompt: str) -> str: ...


class GeminiGenerator:
    """Thin wrapper around the google-genai SDK.

    Tries each model in `models` until one answers, so a renamed/retired model
    ID doesn't take the whole app down.
    """

    def __init__(self, api_key: str, models: tuple[str, ...] = DEFAULT_MODELS) -> None:
        from google import genai  # lazy import: only paid for when AI is actually used
        from google.genai import types

        self._types = types
        self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=AI_TIMEOUT_MS))
        self._models = models

    def generate(self, prompt: str) -> str:
        config = self._types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=AI_TEMPERATURE,
            max_output_tokens=AI_MAX_OUTPUT_TOKENS,
            response_mime_type="application/json",  # ask Gemini for JSON, not prose
        )
        last_error: Exception | None = None
        for model in self._models:
            try:
                response = self._client.models.generate_content(model=model, contents=prompt, config=config)
                if response.text:
                    return response.text
            except Exception as exc:  # SDK raises many types; we log and try the next model
                last_error = exc
                logger.warning("Gemini model %s failed: %s", model, type(exc).__name__)
        raise RuntimeError("All Gemini models failed") from last_error


def _clean_list(value: object) -> tuple[str, ...]:
    """Keep only non-empty strings, cleaned and capped to MAX_IDEAS_PER_LIST."""
    if not isinstance(value, list):
        return ()
    cleaned = (clean_text(item, 160) for item in value if isinstance(item, str))
    return tuple(item for item in cleaned if item)[:MAX_IDEAS_PER_LIST]


def parse_ideas(raw: str) -> Ideas | None:
    """Turn the model's JSON text into Ideas; None if it is unusable."""
    text = raw.strip()
    # Some models wrap JSON in ```json fences even when asked not to.
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not all(key in data for key in IDEA_KEYS):
        return None
    concept = clean_text(data.get("theme_concept"), 240) if isinstance(data.get("theme_concept"), str) else ""
    ideas = Ideas(
        theme_concept=concept,
        decor=_clean_list(data.get("decor")),
        food=_clean_list(data.get("food")),
        activities=_clean_list(data.get("activities")),
        money_saving_tips=_clean_list(data.get("money_saving_tips")),
        source="gemini",
    )
    # An answer with no concept and no ideas is as bad as no answer.
    has_content = concept or any((ideas.decor, ideas.food, ideas.activities, ideas.money_saving_tips))
    return ideas if has_content else None


_OFFLINE = {
    EventType.WEDDING: (
        (
            "Marigold-and-mango-leaf entrance with diya pathways",
            "Fairy-light canopy over the mandap",
            "Family photo wall with old wedding pictures",
        ),
        (
            "Regional thali as the main course",
            "Live chaat and jalebi counter",
            "Welcome drink of thandai or nimbu pani",
        ),
        ("Sangeet with family dance performances", "Mehendi corner with a henna artist", "Couple Q&A game for guests"),
        (
            "Pick a weekday or off-season date for lower venue rates",
            "Use seasonal local flowers",
            "Digital invitations instead of printed cards",
        ),
    ),
    EventType.BIRTHDAY: (
        ("Theme-colour balloon arch", "Photo booth with handmade props", "Name banner and table confetti"),
        ("Theme-shaped cake", "Mini snack boxes for kids", "DIY sandwich or pizza station"),
        ("Treasure hunt", "Musical chairs and passing the parcel", "Memory jar where guests write wishes"),
        ("Host at home or a society hall", "Bulk-buy decor from local markets", "Homemade return gifts"),
    ),
    EventType.COMMUNITY: (
        ("Rangoli competition at the entrance", "LED string lights on the stage", "Volunteer-painted welcome boards"),
        ("Community prasad / bhandara", "Local food stalls run by residents", "Free drinking-water points"),
        (
            "Cultural performances by local children",
            "Health or blood-donation camp",
            "Cleanliness drive after the event",
        ),
        ("Seek local business sponsors", "Borrow tents/chairs from community bodies", "Publicise on WhatsApp groups"),
    ),
}


def offline_ideas(event: EventInput) -> Ideas:
    """Rule-based ideas used when no API key is set or Gemini fails (worst-case path)."""
    decor, food, activities, tips = _OFFLINE[event.event_type]
    theme = event.theme or "a warm, traditional celebration"
    return Ideas(
        theme_concept=f"{event.event_name} in {event.city}: {theme}, planned for {event.guests} guests.",
        decor=decor,
        food=food,
        activities=activities,
        money_saving_tips=tips,
        source="offline",
    )


def generate_ideas(event: EventInput, generator: TextGenerator | None) -> Ideas:
    """Ask Gemini for ideas; fall back to offline ideas on any failure."""
    if generator is None:
        return offline_ideas(event)
    try:
        parsed = parse_ideas(generator.generate(build_ideas_prompt(event)))
    except Exception as exc:  # network, quota, timeout... the user still gets a plan
        logger.warning("Idea generation failed, using offline ideas: %s", type(exc).__name__)
        parsed = None
    return parsed or offline_ideas(event)
