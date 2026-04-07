import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────
# ASSUMPTION A11 — Shortlist Completeness
# ─────────────────────────────────────────────────────────────
ASSUMPTION_ID = "A11"
HYPOTHESIS    = ("The pipeline surfaces ≥3 viable vendor options per category per brief, "
                 "covering the planner's realistic choice set")
METHOD        = ("Run the full pipeline on 5+ test briefs; count how many vendors per "
                 "category reach the shortlist; have a human judge viability of each option")
MIN_SUCCESS   = "≥3 human-judged viable vendors per category in ≥80% of test briefs"

# STATUS: NOT YET TESTED


def run() -> None:
    """
    Placeholder — experiment not yet run.

    Implementation plan:
    1. Define 5+ diverse test event briefs (varying headcount, budget, category mix)
    2. Run full pipeline for each brief end-to-end
    3. Count vendors reaching the shortlist per category
    4. Have a human reviewer judge each shortlisted vendor as viable / not viable
    5. Calculate: briefs with ≥3 viable vendors per category / total briefs
    6. Log results to experiments table
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
