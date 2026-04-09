# tests/fixtures/test_vendors.py
# ─────────────────────────────────────────────────────────────
# Test vendor records used in unit tests and experiment scripts.
# These are representative but do NOT correspond to real vendors.
# ─────────────────────────────────────────────────────────────

TEST_VENDORS = [
    {
        "id":          "test_v001",
        "name":        "Brunswick House",
        "category":    "venue",
        "city":        "London",
        "email":       "events@brunswickhouse.co.uk",
        "website":     "https://www.brunswickhouse.co.uk",
        "description": "A stunning Georgian townhouse with riverside gardens "
                       "and outdoor terraces, ideal for corporate events.",
        "capacity_max": 100,
        "price_from":  3500,
        "price_unit":  "flat",
    },
    {
        "id":          "test_v002",
        "name":        "Social Pantry",
        "category":    "catering",
        "city":        "London",
        "email":       "hello@socialpantry.co.uk",
        "website":     "https://www.socialpantry.co.uk",
        "description": "Award-winning caterers specialising in seasonal, "
                       "sustainable menus for corporate events.",
        "capacity_max": 200,
        "price_from":  75,
        "price_unit":  "per_head",
    },
    {
        "id":          "test_v003",
        "name":        "Team Tactics",
        "category":    "activity",
        "city":        "London",
        "email":       "bookings@teamtactics.co.uk",
        "website":     "https://www.teamtactics.co.uk",
        "description": "Outdoor team building challenges and adventure "
                       "experiences for groups of 10-100.",
        "capacity_max": 100,
        "price_from":  55,
        "price_unit":  "per_head",
    },
    {
        "id":          "test_v004",
        "name":        "The Cooking Academy",
        "category":    "activity",
        "city":        "London",
        "email":       "info@thecookingacademy.co.uk",
        "website":     "https://www.thecookingacademy.co.uk",
        "description": "Interactive cooking classes and team building "
                       "experiences led by professional chefs.",
        "capacity_max": 50,
        "price_from":  70,
        "price_unit":  "per_head",
    },
    {
        "id":          "test_v005",
        "name":        "Lettice Events",
        "category":    "venue",
        "city":        "London",
        "email":       "events@lettice.co.uk",
        "website":     "https://www.lettice.co.uk",
        "description": "Modern event spaces in the heart of London with "
                       "full AV setup and catering kitchen.",
        "capacity_max": 150,
        "price_from":  5000,
        "price_unit":  "flat",
    },
]

# A vendor with no email — used to test email-gate logic
TEST_VENDOR_NO_EMAIL = {
    "id":       "test_v_noemail",
    "name":     "Venue X",
    "category": "venue",
    "city":     "London",
    "email":    None,
    "website":  "https://www.venuex.co.uk",
}

# The default test vendor for rfq_generator and email_sender tests
TEST_VENDOR_DEFAULT = TEST_VENDORS[0]
