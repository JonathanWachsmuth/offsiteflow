import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.collect.api_fetch import run

if __name__ == "__main__":
    results = run(city="London")

    print("\nValidation board entry:")
    print(f"  Assumption:  A1")
    print(f"  Outcome:     {'VALIDATED' if results['validated'] else 'INVALIDATED'}")
    print(f"  Evidence:    {results['total_inserted']} vendors collected via Google Places API")