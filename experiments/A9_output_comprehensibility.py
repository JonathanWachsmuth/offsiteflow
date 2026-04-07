import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────
# ASSUMPTION A9 — Output Comprehensibility
# ─────────────────────────────────────────────────────────────
ASSUMPTION_ID = "A9"
HYPOTHESIS    = ("The generated vendor shortlist is clear and complete enough for a "
                 "planner to make a confident booking decision without further research")
METHOD        = ("Show generated shortlists to 5+ target users (office managers / PAs); "
                 "ask: 'Could you make a booking decision from this?' and rate confidence 1–5; "
                 "note what information is missing or confusing")
MIN_SUCCESS   = "≥80% of test users rate confidence ≥4/5; no critical missing field reported by >1 user"

# STATUS: NOT YET TESTED


def run() -> None:
    """
    Placeholder — experiment not yet run.

    Implementation plan:
    1. Generate 3–5 shortlists using the full pipeline on real briefs
    2. Recruit 5+ target users (office managers, EAs, PAs)
    3. Present each shortlist and ask comprehensibility questions
    4. Collect ratings and open-ended feedback
    5. Identify most frequently missing / confusing fields
    6. Log qualitative + quantitative results to experiments table
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
