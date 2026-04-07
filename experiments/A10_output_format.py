import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────
# ASSUMPTION A10 — Output Format
# ─────────────────────────────────────────────────────────────
ASSUMPTION_ID = "A10"
HYPOTHESIS    = ("The comparison view format (table / card / PDF) fits naturally into a "
                 "planner's existing workflow and requires no explanation to use")
METHOD        = ("Present 2–3 format variants to target users; ask which they would "
                 "forward to a stakeholder / use to approve a booking; collect preference "
                 "and usability ratings")
MIN_SUCCESS   = "≥70% of users prefer the same format variant; rated easy to use by ≥80%"

# STATUS: NOT YET TESTED


def run() -> None:
    """
    Placeholder — experiment not yet run.

    Implementation plan:
    1. Produce the same shortlist in 2–3 format variants:
       - Markdown table (for email / Notion)
       - Card layout (for web UI)
       - PDF summary (for stakeholder approval)
    2. Show all variants to 5+ target users
    3. Ask: 'Which would you send to your manager to approve?'
    4. Record preference, ease-of-use rating, and qualitative notes
    5. Log results to experiments table
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
