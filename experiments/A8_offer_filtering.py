import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────
# ASSUMPTION A8 — Offer Qualification and Filtering
# ─────────────────────────────────────────────────────────────
ASSUMPTION_ID = "A8"
HYPOTHESIS    = ("The system can automatically rank and filter normalised vendor offers "
                 "to surface the most relevant options for a given event brief")
METHOD        = ("Apply scoring rules (budget fit, capacity match, category relevance, "
                 "rating) to normalised offers; compare ranked output against human ranking "
                 "of the same offer set; measure rank-order agreement")
MIN_SUCCESS   = "Top-3 system-ranked offers match human top-3 in ≥80% of test cases"

# STATUS: NOT YET TESTED


def run() -> None:
    """
    Placeholder — experiment not yet run.

    Implementation plan:
    1. Use normalised offers from A7 experiment
    2. Define scoring function: budget_fit, capacity_fit, rating, response_quality
    3. Rank offers per brief using scoring function
    4. Have a human rank the same offers independently
    5. Compare system top-3 vs human top-3 across N briefs
    6. Log agreement rate to experiments table
    """
    print(f"[{ASSUMPTION_ID}] NOT YET RUN")
    return None


if __name__ == "__main__":
    results = run()

    print("\n" + "=" * 55)
    print("  VALIDATION BOARD")
    print("=" * 55)
    print(f"  Assumption:  {ASSUMPTION_ID}")
    print(f"  Hypothesis:  {HYPOTHESIS}")
    print(f"  Min success: {MIN_SUCCESS}")
    print(f"  Result:      NOT YET RUN")
    print(f"  Outcome:     PENDING")
    print("=" * 55)
