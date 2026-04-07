import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────
# ASSUMPTION A7 — Offer Normalisation
# ─────────────────────────────────────────────────────────────
ASSUMPTION_ID = "A7"
HYPOTHESIS    = ("Extracted vendor offer data can be normalised into a consistent, "
                 "comparable format regardless of how each vendor structures their reply")
METHOD        = ("Take extracted offer dicts from A5; apply normalisation rules "
                 "(currency conversion, unit standardisation, missing-field imputation); "
                 "manually review output for consistency and completeness")
MIN_SUCCESS   = ("≥90% of offers normalised without manual intervention; "
                 "all comparable fields populated or marked as unavailable")

# STATUS: NOT YET TESTED


def run() -> None:
    """
    Placeholder — experiment not yet run.

    Implementation plan:
    1. Take extracted offer structs from A5 experiment
    2. Define canonical offer schema (price_per_head_gbp, capacity, date, inclusions list)
    3. Write normalisation rules: currency → GBP, per-person vs. flat fee, etc.
    4. Apply normalisation to each offer
    5. Manually audit 20+ normalised offers for correctness
    6. Log result to experiments table
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
