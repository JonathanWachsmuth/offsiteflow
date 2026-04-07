import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────
# ASSUMPTION A3 — Vendor Response Reliability
# ─────────────────────────────────────────────────────────────
ASSUMPTION_ID = "A3"
HYPOTHESIS    = "≥50% of vendors respond to an automated RFQ email within 72 hours"
METHOD        = ("Send templated RFQ emails to a sample of vendors with extractable emails; "
                 "record responses within a 72-hour window; calculate response rate")
MIN_SUCCESS   = "≥50% response rate within 72 hours across sampled vendors"

# STATUS: NOT YET TESTED


def run() -> None:
    """
    Placeholder — experiment not yet run.

    Implementation plan:
    1. Sample N vendors from vendors table where email IS NOT NULL
    2. Send each a templated RFQ via SMTP / SendGrid
    3. Poll inbox (or webhook) for replies over 72 hours
    4. Record responded = True/False per vendor
    5. Calculate response_rate = responded / sent
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
