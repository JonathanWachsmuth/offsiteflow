# pipeline/normalise/ranker.py
# ─────────────────────────────────────────────────────────────
# Ranks normalised quotes against the event brief.
# Tests assumption A8: system can filter and rank offers
# automatically without human review.
#
# Scoring dimensions:
#   1. Budget fit   (40%) — closeness to category budget allocation
#   2. Completeness (30%) — inclusions coverage
#   3. Confidence   (20%) — extraction reliability
#   4. Value        (10%) — price vs category peer average
# ─────────────────────────────────────────────────────────────

import json
import uuid
import logging

import anthropic

from config.settings import ANTHROPIC_API_KEY, LLM_MODEL
from db.connection import get_db

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

WEIGHTS = {
    "budget_fit":   0.40,
    "completeness": 0.30,
    "confidence":   0.20,
    "value":        0.10,
}


# ─────────────────────────────────────────────────────────────
# SCORING FUNCTIONS
# ─────────────────────────────────────────────────────────────

def score_budget_fit(total_inc_vat: float, budget: float, category: str) -> float:
    """
    Scores how well the quote fits the per-category budget allocation.
    Peaks at exact allocation, degrades outside. >20% over = heavy penalty.
    """
    if not total_inc_vat or not budget:
        return 0.5

    allocations = {
        "venue":         0.50,
        "catering":      0.30,
        "activity":      0.25,
        "transport":     0.05,
        "accommodation": 0.20,
    }
    category_budget = budget * allocations.get(category, 0.30)
    ratio = total_inc_vat / category_budget

    if ratio <= 0:
        return 0.0
    elif ratio <= 0.70:
        return 0.6 + (ratio / 0.70) * 0.2
    elif ratio <= 1.0:
        return 0.8 + ((1.0 - ratio) / 0.30) * 0.2
    elif ratio <= 1.20:
        return 0.8 - ((ratio - 1.0) / 0.20) * 0.4
    else:
        return max(0.0, 0.4 - ((ratio - 1.20) / 0.30) * 0.4)


def score_completeness(completeness_score: float, missing: list, category: str) -> float:
    """
    Scores based on package completeness.
    Bonus for cross-category inclusions (e.g. venue that includes catering).
    """
    if completeness_score is None:
        return 0.5

    bonus = 0.0
    if category == "venue":
        if "catering"      not in (missing or []):
            bonus += 0.10
        if "av_equipment"  not in (missing or []):
            bonus += 0.05

    return min(1.0, completeness_score + bonus)


def score_confidence(confidence_score: float) -> float:
    """Passes through the extraction confidence score."""
    return confidence_score if confidence_score is not None else 0.5


def score_value(total_per_head: float, category: str, peers: list) -> float:
    """
    Scores value relative to category peers.
    Middle-of-market scores highest.
    """
    if not total_per_head or not peers:
        return 0.5

    peer_prices = [
        p["normalised"]["total_per_head"]
        for p in peers
        if p.get("normalised", {}).get("total_per_head")
        and p.get("category") == category
    ]

    if len(peer_prices) < 2:
        return 0.5

    min_p   = min(peer_prices)
    max_p   = max(peer_prices)
    range_p = max_p - min_p

    if range_p == 0:
        return 0.8

    position = (total_per_head - min_p) / range_p
    return max(0.0, min(1.0, 1.0 - abs(position - 0.4) * 1.5))


# ─────────────────────────────────────────────────────────────
# AVAILABILITY GATE
# ─────────────────────────────────────────────────────────────

def passes_availability_gate(quote: dict) -> bool:
    """Returns False only if vendor explicitly said unavailable."""
    return quote.get("availability") != 0


# ─────────────────────────────────────────────────────────────
# COMPOSITE SCORER
# ─────────────────────────────────────────────────────────────

def compute_score(quote: dict, brief: dict, all_quotes: list) -> dict:
    """Computes composite ranking score for one quote."""
    normalised = quote.get("normalised", {})
    category   = quote.get("category", "venue")
    missing    = quote.get("missing_components", [])

    budget_score  = score_budget_fit(
        normalised.get("total_inc_vat"), brief.get("budget_total"), category
    )
    completeness  = score_completeness(
        normalised.get("completeness_score"), missing, category
    )
    confidence    = score_confidence(quote.get("confidence_score"))
    value         = score_value(
        normalised.get("total_per_head"), category, all_quotes
    )

    total = (
        budget_score * WEIGHTS["budget_fit"] +
        completeness * WEIGHTS["completeness"] +
        confidence   * WEIGHTS["confidence"] +
        value        * WEIGHTS["value"]
    )

    return {
        "total":        round(total, 4),
        "budget_fit":   round(budget_score, 4),
        "completeness": round(completeness, 4),
        "confidence":   round(confidence, 4),
        "value":        round(value, 4),
    }


# ─────────────────────────────────────────────────────────────
# LLM RECOMMENDATION
# ─────────────────────────────────────────────────────────────

def generate_recommendation(ranked_quotes: list, brief: dict) -> str:
    """Writes a concise 2-3 sentence planner recommendation."""
    summary = [
        {
            "rank":          q["rank"],
            "vendor":        q["vendor_name"],
            "category":      q["category"],
            "total_inc_vat": q["normalised"].get("total_inc_vat"),
            "per_head":      q["normalised"].get("total_per_head"),
            "score":         q["rank_score"],
            "included":      [c for c, s in q["components"].items() if s == "included"],
            "missing":       q["missing_components"],
        }
        for q in ranked_quotes[:6]
    ]

    prompt = f"""
You are advising a corporate event planner on vendor selection.

EVENT:
- Type:      {brief.get('event_type', 'offsite')}
- Headcount: {brief.get('headcount')} people
- Budget:    £{brief.get('budget_total')}
- City:      {brief.get('city')}
- Needs:     {brief.get('requirements', '')}

TOP RANKED VENDORS:
{json.dumps(summary, indent=2)}

Write a concise 2-3 sentence recommendation for the planner.
Focus on: which combination of vendors best covers the event needs
within budget, and what to watch out for (missing components, budget gaps).
Keep it practical — this is tool output, not a sales pitch.
Return only the recommendation text, nothing else.
"""

    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.error("Failed to generate recommendation: %s", exc)
        return f"Recommendation unavailable: {exc}"


# ─────────────────────────────────────────────────────────────
# DATABASE WRITE
# ─────────────────────────────────────────────────────────────

def save_shortlist(conn, event_id: str, ranked_quotes: list) -> str:
    """Saves ranked shortlist to shortlists + shortlist_items. Returns shortlist_id."""
    shortlist_id = str(uuid.uuid4())

    conn.execute("""
        INSERT INTO shortlists (id, event_id, status) VALUES (?, ?, 'active')
    """, (shortlist_id, event_id))

    for q in ranked_quotes:
        conn.execute("""
            INSERT INTO shortlist_items (
                id, shortlist_id, quote_id, rank, rank_score, rank_reason, selected
            ) VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (
            str(uuid.uuid4()),
            shortlist_id,
            q.get("quote_id"),
            q["rank"],
            q["rank_score"],
            q.get("rank_reason", "")
        ))

    return shortlist_id


# ─────────────────────────────────────────────────────────────
# MAIN RANKER
# ─────────────────────────────────────────────────────────────

def rank_quotes(normalised_quotes: list, brief: dict,
                event_id: str = None, save_to_db: bool = False) -> dict:
    """
    Ranks normalised quotes and produces a shortlist.

    Args:
        normalised_quotes: output from normaliser.normalise_quotes()
        brief:             structured event brief
        event_id:          links shortlist to event (required if save_to_db)
        save_to_db:        write shortlist to database

    Returns:
        {
            "ranked":         [...quotes sorted by score...],
            "by_category":    {category: [top 3 quotes]},
            "recommendation": str,
            "shortlist_id":   str or None,
            "total_ranked":   int,
            "excluded":       int
        }
    """
    logger.info("Ranking %d quotes", len(normalised_quotes))
    print(f"\n  Ranking {len(normalised_quotes)} quotes...")

    available = [q for q in normalised_quotes if passes_availability_gate(q)]
    excluded  = len(normalised_quotes) - len(available)

    if excluded:
        logger.info("Excluded %d unavailable vendors", excluded)
        print(f"  Excluded {excluded} unavailable vendors")

    scored = []
    for q in available:
        scores   = compute_score(q, brief, available)
        q_scored = {**q, "rank_score": scores["total"], "score_breakdown": scores}
        scored.append(q_scored)

    scored.sort(key=lambda x: x["rank_score"], reverse=True)

    for i, q in enumerate(scored, 1):
        q["rank"] = i
        q["rank_reason"] = (
            f"Score {q['rank_score']:.2f} — "
            f"budget fit: {q['score_breakdown']['budget_fit']:.2f}, "
            f"completeness: {q['score_breakdown']['completeness']:.2f}, "
            f"confidence: {q['score_breakdown']['confidence']:.2f}"
        )

    by_category: dict[str, list] = {}
    for q in scored:
        cat = q["category"]
        if cat not in by_category:
            by_category[cat] = []
        if len(by_category[cat]) < 3:
            by_category[cat].append(q)

    logger.info("Generating LLM recommendation")
    print("  Generating recommendation...")
    recommendation = generate_recommendation(scored, brief)

    shortlist_id = None
    if save_to_db and event_id:
        try:
            with get_db() as conn:
                shortlist_id = save_shortlist(conn, event_id, scored)
            logger.info("Shortlist saved: %s", shortlist_id)
            print(f"  Shortlist saved: {shortlist_id}")
        except Exception as exc:
            logger.error("Failed to save shortlist: %s", exc)

    return {
        "ranked":         scored,
        "by_category":    by_category,
        "recommendation": recommendation,
        "shortlist_id":   shortlist_id,
        "total_ranked":   len(scored),
        "excluded":       excluded,
    }
