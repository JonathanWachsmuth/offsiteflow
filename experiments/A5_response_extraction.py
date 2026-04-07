import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────
# ASSUMPTION A5 — Vendor Response Data Extraction
# ─────────────────────────────────────────────────────────────
ASSUMPTION_ID = "A5"
HYPOTHESIS    = ("An LLM can extract structured pricing and availability data from vendor "
                 "email responses with ≥80% accuracy")
METHOD        = ("Collect real vendor reply emails; prompt Claude to extract key fields "
                 "(price, availability, capacity, inclusions); compare against manual labels")
MIN_SUCCESS   = "≥80% field extraction accuracy across 20+ vendor replies"

# STATUS: NOT YET TESTED


def run() -> None:
    """
    Placeholder — experiment not yet run.

    Implementation plan:
    1. Gather a sample of real vendor reply emails (from A3 run)
    2. Define extraction schema: price_per_head, total_price, availability,
       capacity, inclusions, exclusions, validity_period
    3. Prompt Claude to extract fields from each reply
    4. Compare extracted values against manually labelled ground truth
    5. Calculate per-field and overall accuracy
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
