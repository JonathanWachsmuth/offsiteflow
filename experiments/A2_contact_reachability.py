# experiments/A2_vendor_availability.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.collect.contact_extractor import run

if __name__ == "__main__":
    # Run on first 50 vendors to test — remove limit for full run
    results = run(limit=50)

    print("Validation board entry:")
    print(f"  Assumption:  A2")
    print(f"  Outcome:     {'VALIDATED' if results['validated'] else 'INVALIDATED'}")
    print(f"  Evidence:    {results['emails_found']}/{results['total_processed']} "
          f"vendors had extractable email ({results['reachable_pct']}%)")