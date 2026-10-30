"""Utsav AI — GenAI-powered celebration & event planner.

Package layout (each module has ONE job, so it can be tested on its own):

    models      -> typed data containers shared by every other module
    constants   -> all tunable numbers / lists in one place (no magic values)
    validation  -> cleans and checks user input before anything else sees it
    budget      -> splits a total budget into categories (pure maths, no AI)
    timeline    -> turns the event date into a dated to-do countdown
    checklist   -> vendor checklist + questions to ask each vendor
    prompts     -> builds the single Gemini prompt (kept separate for review)
    ai          -> talks to Gemini, parses JSON, falls back safely on failure
    planner     -> orchestrates all of the above into one Plan object
    export      -> Markdown / PDF / calendar (.ics) downloads

Flow: app.py -> validation -> planner -> (budget, timeline, checklist, ai) -> export
"""

__version__ = "1.0.0"
