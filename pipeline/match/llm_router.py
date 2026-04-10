# pipeline/match/llm_router.py
# ─────────────────────────────────────────────────────────────
# LLM Router — parses event brief and matches vendors.
#
# Flow:
#   1. parse_brief()    free text → structured JSON
#   2. prefilter()      SQL filter by city + category
#   3. rank_vendors()   LLM semantic ranking
#   4. route()          orchestrates all three
# ─────────────────────────────────────────────────────────────

import json
import logging

import anthropic

from config.settings import (
    ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS,
    TOP_N_PER_CATEGORY, MAX_CANDIDATES
)
from db.supabase_client import sb

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ─────────────────────────────────────────────────────────────
# BRIEF PARSING
# ─────────────────────────────────────────────────────────────

def parse_brief(brief_input: str | dict) -> dict:
    """
    Converts a free-text brief into structured JSON.
    If already a dict, validates and returns it.
    """
    if isinstance(brief_input, dict):
        return _validate_brief(brief_input)

    logger.info("Parsing free-text event brief via LLM")

    prompt = f"""
You are parsing a corporate event brief for an event planning system.
Extract the structured information and return ONLY valid JSON with no
additional text, markdown, or explanation.

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

    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        brief = json.loads(raw.strip())
        return _validate_brief(brief)

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM brief response as JSON: %s", exc)
        raise ValueError(f"LLM returned invalid JSON for brief: {exc}") from exc
    except Exception as exc:
        logger.error("LLM brief parsing failed: %s", exc)
        raise


def _validate_brief(brief: dict) -> dict:
    """Ensures required fields exist with sensible defaults."""
    brief.setdefault("city",         "London")
    brief.setdefault("headcount",    None)
    brief.setdefault("budget_total", None)
    brief.setdefault("categories",   ["venue", "catering"])
    brief.setdefault("requirements", "")
    brief.setdefault("event_type",   "offsite")
    return brief


# ─────────────────────────────────────────────────────────────
# SQL PRE-FILTER
# ─────────────────────────────────────────────────────────────

def prefilter(brief: dict, category: str) -> list[dict]:
    """
    Filters vendors by city + category using Supabase.
    Optionally filters by capacity.
    Returns up to MAX_CANDIDATES vendor dicts.
    """
    fields = (
        "id,name,category,subcategory,description,amenities,tags,"
        "capacity_min,capacity_max,price_from,price_unit,currency,"
        "email,website,rating_external,verified"
    )
    city = brief["city"].lower()

    query = (
        sb.table("vendors")
        .select(fields)
        .eq("category", category)
        .ilike("city", city)
    )

    if brief.get("headcount"):
        # capacity_max IS NULL or >= headcount — Supabase doesn't support OR on same col cleanly
        # so we fetch without capacity filter and filter in Python
        pass

    result = query.limit(MAX_CANDIDATES * 3).execute()
    rows = result.data or []

    # Python-side capacity filter and sort
    headcount = brief.get("headcount")
    if headcount:
        rows = [r for r in rows if r.get("capacity_max") is None or r["capacity_max"] >= headcount]

    # Sort: verified first, then has_email, then rating desc
    rows.sort(key=lambda r: (
        -int(bool(r.get("verified"))),
        -int(bool(r.get("email"))),
        -(r.get("rating_external") or 0),
    ))

    return rows[:MAX_CANDIDATES]


# ─────────────────────────────────────────────────────────────
# LLM RANKING
# ─────────────────────────────────────────────────────────────

def rank_vendors(brief: dict, candidates: list[dict], category: str) -> list[dict]:
    """
    Asks LLM to rank candidates against the brief.
    Returns top TOP_N_PER_CATEGORY vendors with reasoning.
    """
    if not candidates:
        return []

    vendor_list = [
        {
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
        for v in candidates
    ]

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
            "reason": "one sentence explanation"
        }}
    ]
}}

Rank 1 = best fit. Score = 0.0 to 1.0.
Fewer than {TOP_N_PER_CATEGORY} is fine if others are poor matches.
"""

    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result   = json.loads(raw.strip())
        selected = result.get("selected", [])

    except json.JSONDecodeError as exc:
        logger.error("LLM ranking returned invalid JSON for %s: %s", category, exc)
        return []
    except Exception as exc:
        logger.error("LLM ranking failed for %s: %s", category, exc)
        return []

    vendor_map = {v["id"]: v for v in candidates}
    enriched   = []
    for item in selected:
        vendor = vendor_map.get(item["id"])
        if not vendor:
            logger.warning("LLM returned unknown vendor id: %s", item["id"])
            continue
        enriched.append({**vendor, "rank": item["rank"],
                         "score": item["score"], "reason": item["reason"]})

    return sorted(enriched, key=lambda x: x["rank"])


# ─────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────

def route(brief_input: str | dict) -> dict:
    """
    Parses a brief and returns matched vendors per category.

    Returns:
        {
            "brief":         { structured brief },
            "matches":       { category: [vendors] },
            "total_matched": int
        }
    """
    logger.info("Starting LLM router")

    print(f"\n{'='*55}")
    print(f"  LLM Router — Matching vendors to brief")
    print(f"{'='*55}\n")

    brief = parse_brief(brief_input)

    logger.info(
        "Brief parsed — %s in %s, %s people, £%s",
        brief.get("event_type"), brief.get("city"),
        brief.get("headcount"), brief.get("budget_total")
    )
    print(f"  Event:      {brief.get('event_type')} in {brief.get('city')}")
    print(f"  Headcount:  {brief.get('headcount')}")
    print(f"  Budget:     £{brief.get('budget_total')}")
    print(f"  Categories: {', '.join(brief.get('categories', []))}")
    print(f"  Needs:      {brief.get('requirements')}\n")

    matches = {}

    for category in brief.get("categories", []):
        logger.info("Routing category: %s", category)
        print(f"  Matching {category}s...")

        candidates = prefilter(brief, category)
        logger.debug("Supabase prefilter: %d candidates for %s", len(candidates), category)
        print(f"    Supabase filter: {len(candidates)} candidates")

        if not candidates:
            logger.warning("No vendors found for %s in %s", category, brief["city"])
            print(f"    No vendors found for {category} in {brief['city']}")
            matches[category] = []
            continue

        ranked = rank_vendors(brief, candidates, category)
        matches[category] = ranked
        print(f"    LLM selected: {len(ranked)} vendors")

        for v in ranked:
            print(f"      {v['rank']}. {v['name'][:40]:<40} "
                  f"score: {v['score']} — {v['reason'][:60]}")

    total = sum(len(v) for v in matches.values())
    logger.info("Routing complete — %d vendors matched", total)

    print(f"\n{'='*55}")
    print(f"  ROUTING COMPLETE — {total} vendors matched")
    print(f"{'='*55}\n")

    return {"brief": brief, "matches": matches, "total_matched": total}
