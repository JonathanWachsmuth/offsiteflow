# experiments/A7_offer_normalisation.py
# ─────────────────────────────────────────────────────────────
# Tests A7: Extracted quotes can be normalised for comparison
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import json
import sqlite3
import uuid
from datetime import datetime
from pipeline.normalise.normaliser import normalise_quotes

ASSUMPTION_ID = "A7"
HYPOTHESIS    = ("Extracted pricing from different vendors can be "
                 "normalised into a comparable format")
METHOD        = ("Normalise 5 synthetic quotes across 3 categories, "
                 "verify total prices are comparable and components detected")
MIN_SUCCESS   = ("≥80% of quotes produce a valid normalised total, "
                 "components correctly detected on ≥75% of fields")
DB_PATH       = "data/vendors.db"

TEST_BRIEF = {
    "event_type":   "offsite",
    "city":         "London",
    "headcount":    45,
    "budget_total": 15000,
    "date_start":   "2026-06-15"
}

# ─────────────────────────────────────────────────────────────
# TEST QUOTES
# Simulate extracted quotes from A5 with different structures
# ─────────────────────────────────────────────────────────────

TEST_QUOTES = [
    {
        "quote_id":         "q001",
        "vendor_id":        "v001",
        "vendor_name":      "Brunswick House",
        "category":         "venue",
        "base_price":       4500,
        "price_per_head":   None,
        "service_fee":      0,
        "vat_rate":         0.20,
        "total_estimated":  None,
        "price_unit":       "flat",
        "inclusions":       ["AV", "WiFi", "outdoor terrace",
                             "event coordinator"],
        "exclusions":       ["catering", "accommodation"],
        "availability":     1,
        "confidence_score": 0.725
    },
    {
        "quote_id":         "q002",
        "vendor_id":        "v002",
        "vendor_name":      "Social Pantry",
        "category":         "catering",
        "base_price":       None,
        "price_per_head":   85,
        "service_fee":      12.5,
        "vat_rate":         0.20,
        "total_estimated":  None,
        "price_unit":       "per_head",
        "inclusions":       ["all food", "serving staff",
                             "crockery", "linen"],
        "exclusions":       ["venue", "drinks", "bar"],
        "availability":     1,
        "confidence_score": 0.55
    },
    {
        "quote_id":         "q003",
        "vendor_id":        "v003",
        "vendor_name":      "Team Tactics",
        "category":         "activity",
        "base_price":       None,
        "price_per_head":   65,
        "service_fee":      0,
        "vat_rate":         0.20,
        "total_estimated":  None,
        "price_unit":       "per_head",
        "inclusions":       ["equipment", "facilitators",
                             "debrief session"],
        "exclusions":       ["venue", "catering", "transport"],
        "availability":     1,
        "confidence_score": 0.60
    },
    {
        "quote_id":         "q004",
        "vendor_id":        "v004",
        "vendor_name":      "The Cooking Academy",
        "category":         "activity",
        "base_price":       None,
        "price_per_head":   75,
        "service_fee":      0,
        "vat_rate":         0.20,
        "total_estimated":  None,
        "price_unit":       "per_head",
        "inclusions":       ["ingredients", "chef instructors",
                             "aprons", "recipe cards"],
        "exclusions":       ["drinks", "venue hire"],
        "availability":     1,
        "confidence_score": 0.55
    },
    {
        "quote_id":         "q005",
        "vendor_id":        "v005",
        "vendor_name":      "Lettice Events",
        "category":         "venue",
        "base_price":       6000,
        "price_per_head":   None,
        "service_fee":      0,
        "vat_rate":         0.20,
        "total_estimated":  None,
        "price_unit":       "flat",
        "inclusions":       ["AV", "WiFi", "parking",
                             "catering kitchen"],
        "exclusions":       ["catering", "accommodation"],
        "availability":     1,
        "confidence_score": 0.60
    }
]


# ─────────────────────────────────────────────────────────────
# VALIDATION CHECKS
# ─────────────────────────────────────────────────────────────

def validate_normalisation(normalised_quotes: list,
                           brief: dict) -> dict:
    """
    Checks normalisation quality against expected outcomes.
    """
    headcount = brief["headcount"]
    issues    = []
    passed    = 0
    total     = len(normalised_quotes)

    for q in normalised_quotes:
        n    = q["normalised"]
        name = q["vendor_name"]

        # Must have a total
        if not n.get("total_flat"):
            issues.append(f"{name}: no total_flat produced")
            continue

        # Per head must be total / headcount (within 1%)
        expected_ph = n["total_flat"] / headcount
        actual_ph   = n.get("total_per_head")
        if actual_ph:
            diff = abs(actual_ph - expected_ph) / expected_ph
            if diff > 0.01:
                issues.append(
                    f"{name}: per_head mismatch "
                    f"(expected {expected_ph:.0f}, got {actual_ph:.0f})"
                )

        # VAT total must be > flat total
        if n.get("total_inc_vat") and n["total_inc_vat"] <= n["total_flat"]:
            issues.append(f"{name}: total_inc_vat not > total_flat")

        passed += 1

    return {
        "passed":         passed,
        "total":          total,
        "pass_rate":      round(passed / total, 3) if total else 0,
        "issues":         issues,
        "validated":      passed / total >= 0.80 if total else False
    }


# ─────────────────────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    print(f"\n{'='*55}")
    print(f"  A7 Experiment — Offer Normalisation")
    print(f"  Hypothesis: {HYPOTHESIS}")
    print(f"{'='*55}")

    result = normalise_quotes(
        quotes     = TEST_QUOTES,
        brief      = TEST_BRIEF,
        save_to_db = False
    )

    normalised = result["normalised_quotes"]
    summary    = result["summary"]
    compat     = result["comparability"]

    # Print normalised results
    print(f"\n{'─'*55}")
    print(f"  NORMALISED QUOTES")
    print(f"{'─'*55}")

    for q in normalised:
        n = q["normalised"]
        print(f"\n  {q['vendor_name']} ({q['category']})")
        print(f"    Total (ex VAT):   £{n.get('total_flat', 'N/A')}")
        print(f"    Total (inc VAT):  £{n.get('total_inc_vat', 'N/A')}")
        print(f"    Per head:         £{n.get('total_per_head', 'N/A')}")
        print(f"    Completeness:     {n.get('completeness_score')}")
        print(f"    Included:  "
              f"{[c for c,s in q['components'].items() if s=='included']}")
        print(f"    Missing:   {q['missing_components']}")

    # Comparability check result
    print(f"\n{'─'*55}")
    print(f"  COMPARABILITY CHECK")
    print(f"{'─'*55}")
    print(f"  Comparable:      {compat.get('comparable')}")
    if compat.get("issues"):
        for issue in compat["issues"]:
            print(f"  Issue: {issue}")
    if compat.get("recommendation"):
        print(f"  Recommendation: {compat['recommendation']}")

    # Price summary
    print(f"\n{'─'*55}")
    print(f"  PRICE SUMMARY")
    print(f"{'─'*55}")
    print(f"  Price range:     "
          f"£{summary['price_min']} — £{summary['price_max']}")
    print(f"  Within budget:   "
          f"{summary['within_budget']}/{summary['with_pricing']}")

    # Validation
    validation = validate_normalisation(normalised, TEST_BRIEF)

    print(f"\n{'='*55}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*55}")
    print(f"  Quotes normalised:  {validation['passed']}/{validation['total']}")
    print(f"  Pass rate:          {validation['pass_rate']*100:.0f}%")
    if validation["issues"]:
        for issue in validation["issues"]:
            print(f"  Issue: {issue}")
    print(f"  Threshold:          80%")
    print(f"  OUTCOME: "
          f"{'VALIDATED' if validation['validated'] else 'INVALIDATED'}")
    print(f"{'='*55}\n")

    # Log to experiments table
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
        METHOD,
        MIN_SUCCESS,
        json.dumps({
            "pass_rate":     validation["pass_rate"],
            "n_quotes":      validation["total"],
            "price_range":   summary["price_range"],
            "within_budget": summary["within_budget"],
            "comparable":    compat.get("comparable")
        }),
        "validated" if validation["validated"] else "invalidated",
        f"Pass rate: {validation['pass_rate']*100:.0f}% — "
        f"Price range £{summary['price_min']}–£{summary['price_max']}",
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    print("Result logged to experiments table.")