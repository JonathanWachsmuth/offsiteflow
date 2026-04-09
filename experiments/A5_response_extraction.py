# experiments/A5_response_extraction.py
# ─────────────────────────────────────────────────────────────
# Tests A5: LLM extracts pricing data with ≥80% accuracy
# Tests both email and Tally form response types
# ─────────────────────────────────────────────────────────────

import json
import uuid
from datetime import datetime, timezone
from pipeline.extract.quote_parser import parse_quote
from db.connection import get_db

ASSUMPTION_ID = "A5"
HYPOTHESIS    = "LLM extracts key pricing fields with ≥80% accuracy"
METHOD        = "Run extraction on synthetic vendor responses with ground truth comparison"
MIN_SUCCESS   = "Average field accuracy ≥80% across all test cases"

TEST_BRIEF = {
    "event_type":   "offsite",
    "city":         "London",
    "headcount":    45,
    "budget_total": 15000,
    "date_start":   "2026-06-15"
}

# ─────────────────────────────────────────────────────────────
# TEST CASES
# Mix of email and form responses with ground truth
# ─────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "type": "email",
        "vendor": {
            "id": "v001", "name": "Brunswick House",
            "category": "venue"
        },
        "response": """
            Thank you for your enquiry. We'd be delighted to host
            your team offsite.

            For a group of 45 people we can offer exclusive use of
            our main event space and garden. Our pricing for a
            full day hire is £4,500 + VAT (20%).

            This includes: AV equipment, WiFi, dedicated event
            coordinator, and use of outdoor terrace.
            Catering is not included but we work with approved
            caterers.

            We are available on your requested dates in June.
            Maximum capacity for your event style is 60 people.
        """,
        "ground_truth": {
            "base_price":       4500,
            "vat_rate":         0.20,
            "availability":     1,
            "capacity_offered": 60,
            "price_unit":       "flat"
        }
    },
    {
        "type": "email",
        "vendor": {
            "id": "v002", "name": "Social Pantry",
            "category": "catering"
        },
        "response": """
            Hi, thanks for reaching out to Social Pantry.

            For your group of 45 we would quote £85 per head for
            a full day package including morning pastries, working
            lunch, and afternoon snacks.

            Service charge of 12.5% applies. VAT at 20% on top.

            Includes: all food, serving staff, crockery and linen.
            Excludes: venue hire, bar and drinks.

            Confirmed available for June dates.
        """,
        "ground_truth": {
            "price_per_head":   85,
            "service_fee":      12.5,
            "vat_rate":         0.20,
            "availability":     1,
            "price_unit":       "per_head"
        }
    },
    {
        "type": "email",
        "vendor": {
            "id": "v003", "name": "Team Tactics",
            "category": "activity"
        },
        "response": """
            Thank you for your message.

            We can run our outdoor challenge programme for your group.
            Pricing is £65 per person for a half-day session or
            £95 per person for a full day.

            Both options include: all equipment, trained facilitators,
            and a debrief session.

            We are available from June 16th onwards.
            We can accommodate groups of 20-80 people.
        """,
        "ground_truth": {
            "price_per_head":   65,
            "availability":     1,
            "capacity_offered": 80,
            "price_unit":       "per_head"
        }
    },
    {
        "type": "form",
        "vendor": {
            "id": "v004", "name": "The Cooking Academy",
            "category": "activity"
        },
        "response": {
            "available":         "Yes",
            "maximum_capacity":  50,
            "base_price":        None,
            "price_per_head":    75,
            "inclusions":        "ingredients, chef instructors, aprons, recipe cards",
            "exclusions":        "drinks, venue hire",
            "notes":             "Minimum group size 20 people"
        },
        "ground_truth": {
            "price_per_head":   75,
            "availability":     1,
            "capacity_offered": 50
        }
    },
    {
        "type": "form",
        "vendor": {
            "id": "v005", "name": "Lettice Events",
            "category": "venue"
        },
        "response": {
            "available":         "Yes",
            "maximum_capacity":  80,
            "base_price":        6000,
            "price_per_head":    None,
            "inclusions":        "AV, WiFi, parking, catering kitchen",
            "exclusions":        "catering, accommodation",
            "notes":             "Minimum hire 4 hours",
            "price_unit":        "flat"
        },
        "ground_truth": {
            "base_price":       6000,
            "availability":     1,
            "capacity_offered": 80,
            "price_unit":       "flat"
        }
    }
]


# ─────────────────────────────────────────────────────────────
# ACCURACY MEASUREMENT
# ─────────────────────────────────────────────────────────────

def measure_accuracy(extracted: dict, ground_truth: dict) -> dict:
    """
    Compares extracted fields to ground truth.
    Allows 10% tolerance on numeric values.
    """
    correct = 0
    total   = 0
    details = {}

    for field, expected in ground_truth.items():
        if expected is None:
            continue

        actual = extracted.get(field)
        total += 1

        if actual is None:
            details[field] = {
                "expected": expected,
                "actual":   None,
                "correct":  False,
                "note":     "not extracted"
            }
            continue

        if isinstance(expected, (int, float)):
            tolerance  = abs(expected * 0.10)
            is_correct = abs(float(actual) - float(expected)) \
                         <= tolerance
        else:
            is_correct = str(actual).lower() == str(expected).lower()

        if is_correct:
            correct += 1

        details[field] = {
            "expected": expected,
            "actual":   actual,
            "correct":  is_correct
        }

    accuracy = round(correct / total, 3) if total > 0 else 0.0

    return {
        "accuracy": accuracy,
        "correct":  correct,
        "total":    total,
        "details":  details
    }


# ─────────────────────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    print(f"\n{'='*55}")
    print(f"  A5 Experiment — Quote Extraction Accuracy")
    print(f"  Hypothesis: {HYPOTHESIS}")
    print(f"{'='*55}\n")

    all_accuracies   = []
    all_confidences  = []
    email_accuracies = []
    form_accuracies  = []

    for i, case in enumerate(TEST_CASES, 1):
        print(f"Test {i}/{len(TEST_CASES)}: "
              f"{case['vendor']['name']} ({case['type']})")

        result = parse_quote(
            raw_response = case["response"],
            vendor       = case["vendor"],
            brief        = TEST_BRIEF,
            outreach_id  = f"test_outreach_{i}",
            event_id     = "test_event_a5",
            save_to_db   = False
        )

        accuracy = measure_accuracy(
            result["extracted"],
            case["ground_truth"]
        )

        all_accuracies.append(accuracy["accuracy"])
        all_confidences.append(result["confidence_score"])

        if case["type"] == "email":
            email_accuracies.append(accuracy["accuracy"])
        else:
            form_accuracies.append(accuracy["accuracy"])

        print(f"    Field accuracy:     {accuracy['accuracy']*100:.0f}%"
              f" ({accuracy['correct']}/{accuracy['total']} fields)")
        print(f"    Confidence score:   {result['confidence_score']}")
        print(f"    Response type:      {result['response_type']}")

        for field, detail in accuracy["details"].items():
            status = "✓" if detail["correct"] else "✗"
            print(f"      {status} {field:<20} "
                  f"expected={detail['expected']:<10} "
                  f"actual={detail['actual']}")
        print()

    # ── Summary ──
    avg_accuracy   = sum(all_accuracies) / len(all_accuracies)
    avg_confidence = sum(all_confidences) / len(all_confidences)
    avg_email      = sum(email_accuracies) / len(email_accuracies) \
                     if email_accuracies else 0
    avg_form       = sum(form_accuracies) / len(form_accuracies) \
                     if form_accuracies else 0
    validated      = avg_accuracy >= 0.80

    print(f"{'='*55}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*55}")
    print(f"  Test cases:          {len(TEST_CASES)}")
    print(f"  Email avg accuracy:  {avg_email*100:.1f}%")
    print(f"  Form avg accuracy:   {avg_form*100:.1f}%")
    print(f"  Overall accuracy:    {avg_accuracy*100:.1f}%")
    print(f"  Avg confidence:      {avg_confidence:.3f}")
    print(f"  Threshold:           80%")
    print(f"  OUTCOME: {'VALIDATED' if validated else 'INVALIDATED'}")
    print(f"{'='*55}\n")

    # ── Log to experiments table ──
    with get_db() as conn:
        conn.execute("""
            INSERT INTO experiments (
                id, assumption_id, hypothesis, method,
                min_success, result, outcome, notes, run_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            ASSUMPTION_ID,
            HYPOTHESIS,
            f"Extraction on {len(TEST_CASES)} synthetic responses "
            f"({len(email_accuracies)} email, {len(form_accuracies)} form) "
            f"with ground truth comparison",
            MIN_SUCCESS,
            json.dumps({
                "avg_accuracy":   avg_accuracy,
                "avg_confidence": avg_confidence,
                "email_accuracy": avg_email,
                "form_accuracy":  avg_form,
                "n_cases":        len(TEST_CASES)
            }),
            "validated" if validated else "invalidated",
            f"Overall accuracy: {avg_accuracy*100:.1f}% — "
            f"Email: {avg_email*100:.1f}%, Form: {avg_form*100:.1f}%",
            datetime.now(timezone.utc).isoformat()
        ))
    print("Result logged to experiments table.")