# pipeline/collect/api_fetch.py
# ─────────────────────────────────────────────────────────────
# Google Places API vendor collector — exhaustive UK scrape
# ─────────────────────────────────────────────────────────────

import json
import time
import uuid
import logging
from datetime import date

import requests

from config.settings import (
    GOOGLE_API_KEY, RAW_SCRAPED_DIR,
    DEFAULT_CITY, A1_MIN_VENDORS
)
from db.connection import get_db

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# UK CITIES TO SCRAPE
# ─────────────────────────────────────────────────────────────

UK_CITIES = [
    "London",
    "Manchester",
    "Birmingham",
    "Edinburgh",
    "Bristol",
    "Leeds",
    "Glasgow",
    "Liverpool",
    "Brighton",
    "Oxford",
    "Cambridge",
    "Bath",
]

# Countryside / day-trip locations near London
LONDON_SURROUNDS = [
    "Surrey",
    "Hertfordshire",
    "Kent",
    "Oxfordshire",
    "Buckinghamshire",
    "Berkshire",
    "Hampshire",
    "Cotswolds",
    "Norfolk",
    "Suffolk",
]

# ─────────────────────────────────────────────────────────────
# SEARCH QUERIES — exhaustive per category
# ─────────────────────────────────────────────────────────────

SEARCH_QUERIES = {
    "venue": [
        # London — corporate
        "corporate event venue London",
        "private dining room London corporate",
        "conference centre London SME",
        "exclusive hire venue London",
        "meeting room hire London corporate",
        "event space hire London",
        "boardroom hire London",
        "private members club London events",

        # London — offsites / retreats
        "team away day venue London",
        "company offsite venue London",
        "corporate retreat venue near London",
        "countryside retreat day trip London",
        "rural venue corporate hire London",

        # Home counties — countryside venues
        "country house venue Surrey corporate hire",
        "countryside retreat Hertfordshire corporate",
        "manor house venue Kent corporate events",
        "rural event venue Oxfordshire corporate",
        "private estate venue Buckinghamshire",
        "converted barn venue corporate hire Surrey",
        "farm venue corporate events Kent",
        "country hotel venue corporate hire Berkshire",
        "corporate retreat Hampshire countryside",
        "Cotswolds venue corporate hire",

        # Specific venue types
        "rooftop venue hire London corporate",
        "riverside venue London corporate",
        "warehouse venue London corporate hire",
        "loft venue London corporate events",
        "historic venue London corporate hire",
        "boutique hotel venue London corporate",
        "garden venue London corporate hire",
    ],

    "catering": [
        # Corporate catering
        "corporate catering company London",
        "office catering company London",
        "business lunch catering London",
        "event catering company London",
        "working lunch catering London",
        "corporate hospitality catering London",

        # Catering styles
        "BBQ catering corporate London",
        "canape catering corporate London",
        "buffet catering corporate London",
        "street food catering corporate London",
        "sustainable catering corporate London",
        "vegan catering corporate London",
        "fine dining catering corporate London",

        # Outside London
        "corporate catering company Surrey",
        "event catering company Manchester",
        "corporate catering Birmingham",
    ],

    "activity": [
        # Team building — London
        "team building activities London corporate",
        "corporate team building London",
        "team away day activities London",
        "outdoor team building London corporate",
        "indoor team building London corporate",

        # Specific activities — London
        "corporate cooking class London",
        "cocktail making class corporate London",
        "escape room corporate group London",
        "corporate wine tasting London",
        "corporate pottery class London",
        "axe throwing corporate London",
        "virtual reality team building London",
        "corporate quiz night London",
        "treasure hunt corporate London",
        "corporate sports day London",
        "corporate wellbeing workshop London",
        "corporate art class London",
        "corporate comedy evening London",

        # Outside London
        "outdoor team building Surrey corporate",
        "corporate adventure activities Kent",
        "team building Hertfordshire corporate",
        "corporate sailing Thames",
        "corporate cycling event London",
        "go karting corporate London",
        "corporate bowling London",
        "axe throwing corporate London",
    ],

    "transport": [
        # Coach and bus
        "coach hire London corporate",
        "minibus hire London corporate events",
        "corporate transport company London",
        "executive coach hire London",
        "luxury coach hire London corporate",

        # Specialist
        "chauffeur service London corporate events",
        "corporate minibus hire Surrey",
        "event transport company London",
        "coach hire Manchester corporate",
        "private hire bus London corporate",
    ],

    "accommodation": [
        # Corporate stays near London
        "corporate hotel London group booking",
        "hotel event venue London corporate",
        "country house hotel Surrey corporate",
        "boutique hotel Kent corporate retreat",
        "spa hotel corporate retreat London",
        "rural hotel Oxfordshire corporate",
        "conference hotel London corporate",
        "hotel with meeting rooms London",
    ],
}

EXCLUDED_TYPES = [
    "lodging", "restaurant", "bar", "gym",
    "school", "church", "hospital", "store",
    "grocery_or_supermarket", "gas_station",
    "hair_care", "beauty_salon", "dentist",
]


# ─────────────────────────────────────────────────────────────
# GOOGLE PLACES API
# ─────────────────────────────────────────────────────────────

def search_places(query: str) -> list:
    """Calls Google Places Text Search API with pagination."""
    url     = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    results = []
    params  = {"query": query, "key": GOOGLE_API_KEY, "region": "gb"}
    attempts = 0

    while True:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.error("Places API error for '%s': %s", query, exc)
            break

        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            logger.warning("Places status '%s' — query: %s", status, query)
            break

        results.extend(data.get("results", []))
        next_token = data.get("next_page_token")

        if not next_token or attempts >= 2:
            break

        # Wait for token to become valid, retry once if INVALID_REQUEST
        time.sleep(3)
        page_params = {"pagetoken": next_token, "key": GOOGLE_API_KEY}
        try:
            page_resp = requests.get(url, params=page_params, timeout=10)
            page_data = page_resp.json()

            if page_data.get("status") == "INVALID_REQUEST":
                time.sleep(3)
                page_resp = requests.get(url, params=page_params, timeout=10)
                page_data = page_resp.json()

            if page_data.get("status") in ("OK", "ZERO_RESULTS"):
                results.extend(page_data.get("results", []))
                next_token = page_data.get("next_page_token")
            else:
                break
        except Exception:
            break

        attempts += 1

    return results


def get_place_details(place_id: str) -> dict:
    """Fetches website, phone, address for a place."""
    url    = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields":   "name,formatted_address,formatted_phone_number,"
                    "website,rating,user_ratings_total,types,url",
        "key":      GOOGLE_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get("result", {})
    except Exception as exc:
        logger.warning("Place details failed for %s: %s", place_id, exc)
        return {}


# ─────────────────────────────────────────────────────────────
# DATA PROCESSING
# ─────────────────────────────────────────────────────────────

def is_relevant(place: dict) -> bool:
    """Filters out irrelevant place types."""
    types = place.get("types", [])
    return not any(excl in types for excl in EXCLUDED_TYPES)


def map_to_vendor(place: dict, details: dict,
                  category: str, city: str) -> dict:
    return {
        "id":              str(uuid.uuid4()),
        "name":            place.get("name", ""),
        "category":        category,
        "subcategory":     None,
        "city":            city,
        "country":         "GB",
        "address":         details.get("formatted_address", ""),
        "capacity_min":    None,
        "capacity_max":    None,
        "price_from":      None,
        "price_unit":      None,
        "currency":        "GBP",
        "email":           None,
        "phone":           details.get("formatted_phone_number", ""),
        "website":         details.get("website", ""),
        "contact_form":    None,
        "description":     None,
        "amenities":       None,
        "tags":            None,
        "source":          "google_places",
        "source_url":      details.get("url", ""),
        "rating_external": place.get("rating"),
        "rating_count":    place.get("user_ratings_total"),
        "verified":        0,
        "last_verified":   str(date.today()),
    }


# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────

def insert_vendor(conn, vendor: dict) -> bool:
    """Inserts vendor — skips exact name+city duplicates."""
    existing = conn.execute(
        "SELECT id FROM vendors WHERE name = ? AND city = ?",
        (vendor["name"], vendor["city"])
    ).fetchone()

    if existing:
        return False

    conn.execute("""
        INSERT INTO vendors (
            id, name, category, subcategory, city, country, address,
            capacity_min, capacity_max, price_from, price_unit, currency,
            email, phone, website, contact_form, description,
            amenities, tags, source, source_url,
            rating_external, rating_count, verified, last_verified
        ) VALUES (
            :id, :name, :category, :subcategory, :city, :country, :address,
            :capacity_min, :capacity_max, :price_from, :price_unit, :currency,
            :email, :phone, :website, :contact_form, :description,
            :amenities, :tags, :source, :source_url,
            :rating_external, :rating_count, :verified, :last_verified
        )
    """, vendor)
    return True


def log_experiment(conn, results: dict):
    conn.execute("""
        INSERT INTO experiments (
            id, assumption_id, hypothesis, method,
            min_success, result, outcome, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        "A1",
        f"≥{A1_MIN_VENDORS} vendors per city via Google Places",
        f"Text Search: {sum(len(v) for v in SEARCH_QUERIES.values())} queries, city: {results['city']}",
        f"≥{A1_MIN_VENDORS} unique vendors inserted",
        json.dumps(results),
        "validated" if results["validated"] else "invalidated",
        f"Inserted: {results['total_inserted']} — threshold: {A1_MIN_VENDORS}"
    ))


# ─────────────────────────────────────────────────────────────
# SINGLE CITY RUNNER
# ─────────────────────────────────────────────────────────────

def run(city: str = DEFAULT_CITY,
        categories: list = None,
        log: bool = True) -> dict:
    """
    Collects vendors for one city across all categories.
    categories: optionally restrict to subset e.g. ["venue", "catering"]
    """
    import os
    queries = {k: v for k, v in SEARCH_QUERIES.items()
               if not categories or k in categories}

    print(f"\n{'='*55}")
    print(f"  Vendor Collection — {city}")
    print(f"  Categories: {', '.join(queries.keys())}")
    print(f"{'='*55}\n")

    all_raw             = []
    results_by_category = {}

    with get_db() as conn:
        for category, query_list in queries.items():
            print(f"Category: {category.upper()}")
            inserted  = 0
            found     = 0
            seen_ids  = set()

            for query in query_list:
                # Append city to query if not already present
                full_query = query if city.lower() in query.lower() \
                             else f"{query} {city}"
                print(f"  Querying: '{full_query}'")
                places = search_places(full_query)

                for place in places:
                    pid = place.get("place_id")
                    if pid in seen_ids or not is_relevant(place):
                        continue
                    seen_ids.add(pid)
                    found += 1

                    details = get_place_details(pid)
                    time.sleep(0.1)

                    vendor = map_to_vendor(place, details, category, city)
                    all_raw.append({"place": place, "details": details})

                    if insert_vendor(conn, vendor):
                        inserted += 1

            results_by_category[category] = {
                "found": found, "inserted": inserted
            }
            print(f"  → Found: {found} | New: {inserted}\n")

        # Save raw data
        os.makedirs(RAW_SCRAPED_DIR, exist_ok=True)
        raw_path = f"{RAW_SCRAPED_DIR}/google_places_{city.lower()}.json"
        with open(raw_path, "w") as f:
            json.dump(all_raw, f, indent=2)

        total = sum(r["inserted"] for r in results_by_category.values())
        results = {
            "city":           city,
            "total_inserted": total,
            "by_category":    results_by_category,
            "threshold":      A1_MIN_VENDORS,
            "validated":      total >= A1_MIN_VENDORS
        }

        print(f"{'='*55}")
        print(f"  SUMMARY — {city}")
        print(f"{'='*55}")
        for cat, r in results_by_category.items():
            print(f"  {cat:<14} found: {r['found']:<5} new: {r['inserted']}")
        print(f"  {'─'*40}")
        print(f"  TOTAL NEW: {total}")
        print(f"{'='*55}\n")

        if log:
            log_experiment(conn, results)

    return results


# ─────────────────────────────────────────────────────────────
# MULTI-CITY RUNNER
# ─────────────────────────────────────────────────────────────

def run_uk(cities: list = None,
           surrounds: bool = True,
           categories: list = None) -> dict:
    """
    Runs collection across multiple UK cities.
    cities:     list of cities (defaults to UK_CITIES)
    surrounds:  also scrape London countryside locations
    categories: restrict to specific categories
    """
    target_cities = cities or UK_CITIES
    all_results   = {}
    grand_total   = 0

    print(f"\n{'='*55}")
    print(f"  UK-WIDE VENDOR COLLECTION")
    print(f"  Cities: {len(target_cities)}")
    if surrounds:
        print(f"  + {len(LONDON_SURROUNDS)} London surrounds")
    print(f"{'='*55}")

    # Main cities
    for city in target_cities:
        result = run(city=city, categories=categories, log=False)
        all_results[city] = result
        grand_total += result["total_inserted"]
        time.sleep(1)  # brief pause between cities

    # London surrounds (venue + activity only — transport
    # and catering are less relevant for countryside)
    if surrounds:
        surround_cats = categories or ["venue", "activity", "accommodation"]
        for location in LONDON_SURROUNDS:
            result = run(
                city       = location,
                categories = surround_cats,
                log        = False
            )
            all_results[location] = result
            grand_total += result["total_inserted"]
            time.sleep(1)

    print(f"\n{'='*55}")
    print(f"  UK COLLECTION COMPLETE")
    print(f"{'='*55}")
    for city, r in all_results.items():
        print(f"  {city:<20} new: {r['total_inserted']}")
    print(f"  {'─'*40}")
    print(f"  GRAND TOTAL NEW: {grand_total}")
    print(f"{'='*55}\n")

    # Check total DB count
    with get_db() as conn:
        total_in_db = conn.execute(
            "SELECT COUNT(*) FROM vendors"
        ).fetchone()[0]
        print(f"  Total vendors in database: {total_in_db}")

    return {"cities": all_results, "grand_total": grand_total}


# ─────────────────────────────────────────────────────────────
# ENTRY POINTS
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="OffsiteFlow vendor collector")
    parser.add_argument("--city",      type=str, default=None,
                        help="Single city to scrape")
    parser.add_argument("--uk",        action="store_true",
                        help="Scrape all UK cities")
    parser.add_argument("--surrounds", action="store_true", default=True,
                        help="Include London surrounds (default: True)")
    parser.add_argument("--categories", nargs="+", default=None,
                        help="Restrict to specific categories")
    args = parser.parse_args()

    if args.uk:
        run_uk(
            surrounds  = args.surrounds,
            categories = args.categories
        )
    elif args.city:
        run(city=args.city, categories=args.categories)
    else:
        # Default: London only
        run()