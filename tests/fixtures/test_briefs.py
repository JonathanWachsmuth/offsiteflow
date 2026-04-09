# tests/fixtures/test_briefs.py
# ─────────────────────────────────────────────────────────────
# All test event briefs used across experiments and tests.
# Import from here — do not define inline in pipeline files.
# ─────────────────────────────────────────────────────────────

# ── Free-text brief (used by A4, pipeline CLI default) ────────
BRIEF_TEXT_LONDON = """
We need to organise a 2-day team offsite for 45 people in London
in June. Budget is around £15,000 total. We want a venue with
outdoor space, good catering, and a fun team building activity.
Ideally something outside the city centre with a relaxed
countryside feel.
"""

# ── Structured brief (used by A5, A7, A8, run.py) ────────────
BRIEF_STRUCTURED = {
    "event_type":   "offsite",
    "city":         "London",
    "headcount":    45,
    "budget_total": 15000,
    "date_start":   "2026-06-15",
    "requirements": "outdoor space, countryside feel, team building",
    "categories":   ["venue", "catering", "activity"],
}

# ── Additional briefs for A4 accuracy testing ─────────────────
BRIEF_WORKSHOP = {
    "event_type":   "workshop",
    "city":         "Manchester",
    "headcount":    20,
    "budget_total": 5000,
    "date_start":   "2026-07-10",
    "requirements": "projector, breakout rooms, catering",
    "categories":   ["venue", "catering"],
}

BRIEF_TEAM_DINNER = {
    "event_type":   "team_dinner",
    "city":         "London",
    "headcount":    30,
    "budget_total": 4500,
    "date_start":   "2026-05-20",
    "requirements": "private dining room, 3 courses, wine pairing",
    "categories":   ["venue", "catering"],
}
