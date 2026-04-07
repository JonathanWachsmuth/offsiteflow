# experiments/A4_llm_brief_parsing.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.match.llm_router import route

ASSUMPTION_ID = "A4"
HYPOTHESIS    = "LLM can parse a free-text event brief and return relevant vendors"
METHOD        = "Pass test briefs to router, evaluate relevance of returned vendors"
MIN_SUCCESS   = "≥80% of returned vendors are genuinely relevant to the brief"

# Test brief — change this to test different scenarios
TEST_BRIEF = """
We need to organise a 2-day team offsite for 45 people in London in June.
Budget is around £15,000 total. We want a venue with outdoor space,
good catering, and a fun team building activity. Ideally something
outside the city centre with a relaxed countryside feel.
"""

if __name__ == "__main__":
    results = route(TEST_BRIEF)

    print("\nValidation board entry:")
    print(f"  Assumption:  {ASSUMPTION_ID}")
    print(f"  Total matched: {results['total_matched']} vendors")
    print(f"  Categories:    {list(results['matches'].keys())}")