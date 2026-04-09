# tests/fixtures/synthetic_responses.py
# ─────────────────────────────────────────────────────────────
# Synthetic vendor responses used across experiments and tests.
# Mirrors the kinds of replies received from real vendors.
#
# SYNTHETIC_RESPONSES  — one response per vendor category,
#                        keyed by category (used by run.py)
# TEST_CASES           — labelled cases with ground truth
#                        (used by A5 experiment / test_parser)
# ─────────────────────────────────────────────────────────────

# ── Category-keyed responses (used by pipeline/run.py) ───────

SYNTHETIC_RESPONSES = {
    "venue": {
        "type": "email",
        "text": """
            Thank you for your enquiry about hosting your team offsite.
            We would be delighted to accommodate your group.

            For 45 people, we offer exclusive hire of our main space
            and garden. Full day hire: £4,500 + VAT (20%).

            Includes: AV equipment, WiFi, event coordinator,
            outdoor terrace access.
            Excludes: catering, accommodation.

            We are available on your requested June dates.
            Maximum capacity: 60 people.
        """
    },
    "catering": {
        "type": "form",
        "data": {
            "available":         "Yes",
            "maximum_capacity":  80,
            "base_price":        None,
            "price_per_head":    85,
            "inclusions":        "all food, serving staff, crockery, linen",
            "exclusions":        "venue, drinks, bar",
            "notes":             "12.5% service charge applies. VAT at 20%."
        }
    },
    "activity": {
        "type": "email",
        "text": """
            Thanks for getting in touch!

            We can run our outdoor team challenge programme for your group.
            Pricing: £65 per person for half-day, £95 for full day.

            Includes: all equipment, facilitators, debrief session.
            Excludes: venue, catering, transport.

            Available June 15th onwards. We accommodate 20-80 people.
        """
    }
}


# ── Labelled test cases with ground truth (used by A5 / test_parser) ──

TEST_CASES = [
    {
        "type":   "email",
        "vendor": {"id": "v001", "name": "Brunswick House", "category": "venue"},
        "response": """
            Thank you for your enquiry. We'd be delighted to host
            your team offsite.

            For a group of 45 people we can offer exclusive use of
            our main event space and garden. Our pricing for a
            full day hire is £4,500 + VAT (20%).

            This includes: AV equipment, WiFi, dedicated event
            coordinator, and use of outdoor terrace.
            Catering is not included but we work with approved caterers.

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
        "type":   "email",
        "vendor": {"id": "v002", "name": "Social Pantry", "category": "catering"},
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
            "price_per_head": 85,
            "service_fee":    12.5,
            "vat_rate":       0.20,
            "availability":   1,
            "price_unit":     "per_head"
        }
    },
    {
        "type":   "email",
        "vendor": {"id": "v003", "name": "Team Tactics", "category": "activity"},
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
        "type":   "form",
        "vendor": {"id": "v004", "name": "The Cooking Academy", "category": "activity"},
        "response": {
            "available":        "Yes",
            "maximum_capacity": 50,
            "base_price":       None,
            "price_per_head":   75,
            "inclusions":       "ingredients, chef instructors, aprons, recipe cards",
            "exclusions":       "drinks, venue hire",
            "notes":            "Minimum group size 20 people"
        },
        "ground_truth": {
            "price_per_head":   75,
            "availability":     1,
            "capacity_offered": 50
        }
    },
    {
        "type":   "form",
        "vendor": {"id": "v005", "name": "Lettice Events", "category": "venue"},
        "response": {
            "available":        "Yes",
            "maximum_capacity": 80,
            "base_price":       6000,
            "price_per_head":   None,
            "inclusions":       "AV, WiFi, parking, catering kitchen",
            "exclusions":       "catering, accommodation",
            "notes":            "Minimum hire 4 hours",
            "price_unit":       "flat"
        },
        "ground_truth": {
            "base_price":       6000,
            "availability":     1,
            "capacity_offered": 80,
            "price_unit":       "flat"
        }
    }
]
