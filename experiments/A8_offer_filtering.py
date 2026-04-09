# experiments/A8_offer_filtering.py
# ─────────────────────────────────────────────────────────────
# Tests A8: system automatically filters and ranks offers
# without human review
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import json
import sqlite3
import uuid
from datetime import datetime
from pipeline.normalise.ranker import rank_quotes

ASSUMPTION_ID = "A8"
HYPOTHESIS    = ("The system can automatically discard irrelevant "
                 "or non-compliant offers and rank remaining ones "
                 "against the event brief without human review")
MIN_SUCCESS   = ("Unavailable vendors correctly excluded; "
                 "ranked order reflects brief priorities; "
                 "top vendor per category is genuinely the best fit")
DB_PATH       = "data/vendors.db"

TEST_BRIEF = {
    "event_type":   "offsite",
    "city":         "London",
    "headcount":    45,
    "budget_total": 15000,
    "date_start":   "2026-06-15",
    "requirements": "outdoor space, countryside feel, team building"
}

# Mix of available and unavailable quotes
# with different price/completeness profiles
TEST_QUOTES = [
    {
        "quote_id":    "q001",
        "vendor_id":   "v001",
        "vendor_name": "Brunswick House",
        "category":    "venue",
        "availability": 1,
        "confidence_score": 0.725,
        "normalised": {
            "total_flat":        4500,
            "total_per_head":    100,
            "total_inc_vat":     5400,
            "completeness_score": 0.55
        },
        "components": {
            "venue": "included", "av_equipment": "included",
            "staffing": "included", "catering": "excluded"
        },
        "missing_components": ["catering", "accommodation"]
    },
    {
        "quote_id":    "q002",
        "vendor_id":   "v002",
        "vendor_name": "Lettice Events",
        "category":    "venue",
        "availability": 1,
        "confidence_score": 0.60,
        "normalised": {
            "total_flat":        6000,
            "total_per_head":    133,
            "total_inc_vat":     7200,
            "completeness_score": 0.60
        },
        "components": {
            "venue": "included", "av_equipment": "included",
            "catering": "excluded", "staffing": "unknown"
        },
        "missing_components": ["catering"]
    },
    {
        # Unavailable — should be excluded
        "quote_id":    "q003",
        "vendor_id":   "v003",
        "vendor_name": "Venue X (unavailable)",
        "category":    "venue",
        "availability": 0,
        "confidence_score": 0.80,
        "normalised": {
            "total_flat":        3000,
            "total_per_head":    67,
            "total_inc_vat":     3600,
            "completeness_score": 0.70
        },
        "components": {
            "venue": "included", "catering": "included"
        },
        "missing_components": []
    },
    {
        "quote_id":    "q004",
        "vendor_id":   "v004",
        "vendor_name": "Social Pantry",
        "category":    "catering",
        "availability": 1,
        "confidence_score": 0.55,
        "normalised": {
            "total_flat":        4335,
            "total_per_head":    96,
            "total_inc_vat":     5202,
            "completeness_score": 0.35
        },
        "components": {
            "catering": "included", "staffing": "included",
            "venue": "excluded"
        },
        "missing_components": ["venue", "av_equipment"]
    },
    {
        "quote_id":    "q005",
        "vendor_id":   "v005",
        "vendor_name": "Team Tactics",
        "category":    "activity",
        "availability": 1,
        "confidence_score": 0.60,
        "normalised": {
            "total_flat":        2925,
            "total_per_head":    65,
            "total_inc_vat":     3510,
            "completeness_score": 0.25
        },
        "components": {
            "activities": "included", "staffing": "included",
            "venue": "excluded", "catering": "excluded"
        },
        "missing_components": ["venue", "catering"]
    },
    {
        "quote_id":    "q006",
        "vendor_id":   "v006",
        "vendor_name": "The Cooking Academy",
        "category":    "activity",
        "availability": 1,
        "confidence_score": 0.55,
        "normalised": {
            "total_flat":        3375,
            "total_per_head":    75,
            "total_inc_vat":     4050,
            "completeness_score": 0.25
        },
        "components": {
            "activities": "included", "catering": "included",
            "venue": "excluded"
        },
        "missing_components": ["venue"]
    }
]


if __name__ == "__main__":

    print(f"\n{'='*55}")
    print(f"  A8 Experiment — Offer Filtering and Ranking")
    print(f"  Hypothesis: {HYPOTHESIS}")
    print(f"{'='*55}")

    result = rank_quotes(
        normalised_quotes = TEST_QUOTES,
        brief             = TEST_BRIEF,
        save_to_db        = False
    )

    ranked = result["ranked"]

    # ── Print results ──
    print(f"\n{'─'*55}")
    print(f"  RANKED SHORTLIST ({result['total_ranked']} vendors)")
    print(f"  Excluded (unavailable): {result['excluded']}")
    print(f"{'─'*55}")

    for q in ranked:
        print(f"\n  #{q['rank']} {q['vendor_name']} "
              f"({q['category']})")
        print(f"      Score:      {q['rank_score']:.3f}")
        b = q["score_breakdown"]
        print(f"      Budget fit: {b['budget_fit']:.2f}  "
              f"Completeness: {b['completeness']:.2f}  "
              f"Confidence: {b['confidence']:.2f}")
        print(f"      Total:      "
              f"£{q['normalised'].get('total_inc_vat', 'N/A')} inc VAT")
        print(f"      Missing:    {q['missing_components']}")

    print(f"\n{'─'*55}")
    print(f"  BY CATEGORY")
    print(f"{'─'*55}")
    for cat, quotes in result["by_category"].items():
        print(f"\n  {cat.upper()}")
        for q in quotes:
            print(f"    {q['rank']}. {q['vendor_name']:<30} "
                  f"score: {q['rank_score']:.3f}")

    print(f"\n{'─'*55}")
    print(f"  RECOMMENDATION")
    print(f"{'─'*55}")
    print(f"  {result['recommendation']}")

    # ── Validation checks ──
    issues   = []
    passed   = 0

    # Check 1: unavailable vendor excluded
    unavailable_names = [
        q["vendor_name"] for q in ranked
        if q.get("availability") == 0
    ]
    if unavailable_names:
        issues.append(
            f"Unavailable vendors not excluded: {unavailable_names}"
        )
    else:
        passed += 1
        print(f"\n  ✓ Unavailable vendors correctly excluded")

    # Check 2: top venue is Brunswick House
    # (better budget fit than Lettice at £7,200 inc VAT)
    venue_top = result["by_category"].get("venue", [{}])[0]
    if venue_top.get("vendor_name") == "Brunswick House":
        passed += 1
        print(f"  ✓ Top venue correctly ranked "
              f"(Brunswick House — better budget fit)")
    else:
        issues.append(
            f"Top venue was {venue_top.get('vendor_name')} "
            f"— expected Brunswick House"
        )

    # Check 3: Cooking Academy ranks above Team Tactics
    # (includes catering component)
    activity_names = [
        q["vendor_name"]
        for q in result["by_category"].get("activity", [])
    ]
    if (activity_names.index("The Cooking Academy")<
        activity_names.index("Team Tactics")):
        passed += 1
        print(f"  ✓ Activity ranking correct "
              f"(Cooking Academy ranks above Team Tactics)")
    else:
        issues.append(
            "Activity ranking incorrect — "
            "Cooking Academy should rank above Team Tactics"
        )

    validated = len(issues) == 0

    print(f"\n{'='*55}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*55}")
    print(f"  Checks passed: {passed}/3")
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
    print(f"  OUTCOME: "
          f"{'VALIDATED' if validated else 'NEEDS REVIEW'}")
    print(f"{'='*55}\n")

    # ── Log to experiments table ──
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO experiments (
            id, assumption_id, hypothesis, method,
            min_success, result, outcome, notes, run_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        ASSUMPTION_ID,
        HYPOTHESIS,
        f"Ranked {len(TEST_QUOTES)} quotes including "
        f"1 unavailable vendor; verified exclusion and ordering",
        MIN_SUCCESS,
        json.dumps({
            "total_ranked":    result["total_ranked"],
            "excluded":        result["excluded"],
            "checks_passed":   passed,
            "checks_total":    3
        }),
        "validated" if validated else "invalidated",
        f"{passed}/3 ranking checks passed",
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    print("Result logged to experiments table.")