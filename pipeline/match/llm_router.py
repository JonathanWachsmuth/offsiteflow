# pipeline/match/llm_router.py
# ─────────────────────────────────────────────────────────────
# LLM Router — the first piece of the agent
# Takes an event brief → returns matched vendors per category
# Tests assumption A4: LLM can parse brief and route to vendors
#
# Structure:
#   1. parse_brief()     free text → structured JSON
#   2. prefilter()       SQL filter by city + category
#   3. rank_vendors()    LLM semantic ranking
#   4. route()           orchestrates all three steps
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import sqlite3
import anthropic
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "data/vendors.db"
client  = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# How many vendors to return per category
TOP_N_PER_CATEGORY = 5

# How many vendors to send to LLM for ranking (post SQL filter)
MAX_CANDIDATES     = 30


# ─────────────────────────────────────────────────────────────
# JOB 1 — PARSE BRIEF
# Converts free text or dict into structured event brief
# ─────────────────────────────────────────────────────────────

def parse_brief(brief_input: str | dict) -> dict:
    """
    Parses a free-text event brief into structured JSON.
    If already a dict, validates and returns it.

    Returns:
    {
        "city":         "London",
        "headcount":    45,
        "budget_total": 15000,
        "budget_currency": "GBP",
        "event_type":   "offsite",
        "date_start":   "2026-06-15",   # optional
        "date_end":     "2026-06-16",   # optional
        "categories":   ["venue", "catering", "activity"],
        "requirements": "countryside setting, outdoor space, team building",
        "brief_text":   "original input text"
    }
    """
    # Already structured — validate and return
    if isinstance(brief_input, dict):
        return _validate_brief(brief_input)

    # Free text — parse with LLM
    print("  Parsing event brief...")

    prompt = f"""
You are parsing a corporate event brief for an event planning system.
Extract the structured information from this brief and return ONLY 
valid JSON with no additional text, markdown, or explanation.

Brief: "{brief_input}"

Return this exact JSON structure:
{{
    "city": "city name or null",
    "headcount": integer or null,
    "budget_total": number in GBP or null,
    "budget_currency": "GBP",
    "event_type": "offsite|team_dinner|workshop|conference|other",
    "date_start": "YYYY-MM-DD or null",
    "date_end": "YYYY-MM-DD or null",
    "categories": ["venue", "catering", "activity", "transport"],
    "requirements": "key requirements as a short string",
    "brief_text": "{brief_input}"
}}

For categories: include only what the brief requires.
If the brief mentions food/meals include "catering".
If it mentions activities/team building include "activity".
If it mentions travel/coaches include "transport".
Always include "venue" unless explicitly not needed.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    brief = json.loads(raw)
    return _validate_brief(brief)


def _validate_brief(brief: dict) -> dict:
    """Ensures required fields exist with sensible defaults."""
    brief.setdefault("city",          "London")
    brief.setdefault("headcount",     None)
    brief.setdefault("budget_total",  None)
    brief.setdefault("categories",    ["venue", "catering"])
    brief.setdefault("requirements",  "")
    brief.setdefault("event_type",    "offsite")
    return brief


# ─────────────────────────────────────────────────────────────
# JOB 2 — SQL PRE-FILTER
# Fast, cheap filtering before LLM sees anything
# ─────────────────────────────────────────────────────────────

def prefilter(conn: sqlite3.Connection,
              brief: dict,
              category: str) -> list[dict]:
    """
    Filters vendors by city + category using SQL.
    Optionally filters by capacity if headcount provided.
    Returns list of vendor dicts ready for LLM ranking.
    """
    params = [category, brief["city"]]
    query  = """
        SELECT
            id, name, category, subcategory,
            description, amenities, tags,
            capacity_min, capacity_max,
            price_from, price_unit, currency,
            email, website, rating_external
        FROM vendors
        WHERE category = ?
        AND   LOWER(city) = LOWER(?)
    """

    # Filter by capacity if headcount known
    if brief.get("headcount"):
        query += """
            AND (capacity_max IS NULL 
                 OR capacity_max >= ?)
        """
        params.append(brief["headcount"])

    # Prioritise verified vendors and those with emails
    query += """
        ORDER BY
            verified DESC,
            CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END DESC,
            rating_external DESC NULLS LAST
        LIMIT ?
    """
    params.append(MAX_CANDIDATES)

    cursor = conn.cursor()
    cursor.execute(query, params)
    columns = [d[0] for d in cursor.description]
    rows    = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


# ─────────────────────────────────────────────────────────────
# JOB 3 — LLM SEMANTIC RANKING
# Ranks pre-filtered vendors against the brief
# ─────────────────────────────────────────────────────────────

def rank_vendors(brief: dict,
                 candidates: list[dict],
                 category: str) -> list[dict]:
    """
    Asks LLM to rank candidates against the event brief.
    Returns top N vendors with reasoning.
    """
    if not candidates:
        return []

    # Build compact vendor list for the prompt
    vendor_list = []
    for v in candidates:
        entry = {
            "id":          v["id"],
            "name":        v["name"],
            "description": v["description"] or "",
            "amenities":   v["amenities"] or "",
            "tags":        v["tags"] or "",
            "capacity":    f"{v['capacity_min']}-{v['capacity_max']}" 
                           if v["capacity_max"] else "unknown",
            "price_from":  v["price_from"] or "unknown",
            "rating":      v["rating_external"] or "unknown"
        }
        vendor_list.append(entry)

    prompt = f"""
You are matching corporate event vendors to a client brief.

EVENT BRIEF:
- Type:         {brief.get("event_type", "offsite")}
- City:         {brief.get("city")}
- Headcount:    {brief.get("headcount", "unknown")}
- Budget:       £{brief.get("budget_total", "unknown")}
- Requirements: {brief.get("requirements", "none specified")}
- Categories needed: {", ".join(brief.get("categories", []))}

VENDOR CATEGORY: {category}

CANDIDATES:
{json.dumps(vendor_list, indent=2)}

Select the top {TOP_N_PER_CATEGORY} vendors most suitable for this brief.
Consider: relevance to requirements, capacity fit, price range, quality signals.

Return ONLY valid JSON, no markdown, no explanation:
{{
    "selected": [
        {{
            "id": "vendor_id",
            "name": "vendor name",
            "rank": 1,
            "score": 0.95,
            "reason": "one sentence explanation of why this vendor fits"
        }}
    ]
}}

Rank 1 = best fit. Score = 0.0 to 1.0.
Only include vendors that genuinely fit — fewer than {TOP_N_PER_CATEGORY} is fine
if the others are poor matches.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result   = json.loads(raw)
    selected = result.get("selected", [])

    # Enrich with full vendor data
    vendor_map = {v["id"]: v for v in candidates}
    enriched   = []
    for item in selected:
        vendor = vendor_map.get(item["id"])

        # Skip if LLM returned an ID that doesn't exist in candidates
        if not vendor:
            continue

        enriched.append({
            **vendor,
            "rank":   item["rank"],
            "score":  item["score"],
            "reason": item["reason"]
        })

    return sorted(enriched, key=lambda x: x["rank"])


# ─────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# Runs all three jobs and returns matched vendors
# ─────────────────────────────────────────────────────────────

def route(brief_input: str | dict) -> dict:
    """
    Main entry point for the LLM router.
    Takes a brief, returns matched vendors per category.

    Returns:
    {
        "brief":   { structured brief },
        "matches": {
            "venue":     [ top 5 vendors ],
            "catering":  [ top 5 vendors ],
            "activity":  [ top 5 vendors ]
        },
        "total_matched": 15
    }
    """
    print(f"\n{'='*55}")
    print(f"  LLM Router — Matching vendors to brief")
    print(f"{'='*55}\n")

    # Step 1: Parse brief
    brief = parse_brief(brief_input)
    print(f"  Event:      {brief.get('event_type')} in {brief.get('city')}")
    print(f"  Headcount:  {brief.get('headcount')}")
    print(f"  Budget:     £{brief.get('budget_total')}")
    print(f"  Categories: {', '.join(brief.get('categories', []))}")
    print(f"  Needs:      {brief.get('requirements')}\n")

    conn    = sqlite3.connect(DB_PATH)
    matches = {}

    for category in brief.get("categories", []):
        print(f"  Matching {category}s...")

        # Step 2: SQL pre-filter
        candidates = prefilter(conn, brief, category)
        print(f"    SQL filter: {len(candidates)} candidates")

        if not candidates:
            print(f"    No vendors found for {category} in {brief['city']}")
            matches[category] = []
            continue

        # Step 3: LLM ranking
        ranked = rank_vendors(brief, candidates, category)
        matches[category] = ranked
        print(f"    LLM selected: {len(ranked)} vendors")

        for v in ranked:
            print(f"      {v['rank']}. {v['name'][:40]:<40} "
                  f"score: {v['score']} — {v['reason'][:60]}")

    conn.close()

    total = sum(len(v) for v in matches.values())

    print(f"\n{'='*55}")
    print(f"  ROUTING COMPLETE — {total} vendors matched")
    print(f"{'='*55}\n")

    return {
        "brief":         brief,
        "matches":       matches,
        "total_matched": total
    }