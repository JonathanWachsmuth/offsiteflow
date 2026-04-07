# pipeline/collect/api_fetch.py
# ─────────────────────────────────────────────────────────────
# Google Places API vendor collector
# Tests assumption A1: sufficient vendor data accessible via API
# Scalable: pass any city + category to collect vendors
# ─────────────────────────────────────────────────────────────

import os
import json
import time
import sqlite3
import uuid
import requests
from datetime import date
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DB_PATH        = "data/vendors.db"
RAW_OUTPUT     = "data/raw/scraped/google_places_raw.json"

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# Change city and queries here to run in any market
# ─────────────────────────────────────────────────────────────

CITY = "London"

SEARCH_QUERIES = {
    "venue": [
    "corporate event venue London",
    "private dining room London corporate",
    "conference centre London SME",
    "countryside retreat London corporate",
    "team away day venue London",
    "corporate retreat venue Surrey",      # add
    "meeting room hire London",            # add
    "event space hire London",             # add
    "corporate venue Hertfordshire",       # add
    ],
    "catering": [
        "corporate catering company London",
        "event catering London office",
        "business lunch catering London",
    ],
    "activity": [
        "team building activities London corporate",
        "corporate cooking class London",
        "escape room corporate London",
        "outdoor team building London",
    ],
    "transport": [
        "coach hire London corporate",
        "minibus hire London corporate events",
        "corporate transport London",
    ],
}

# Relevance filter — Places API returns noise, this cuts it
EXCLUDED_TYPES = [
    "lodging", "restaurant", "bar", "gym",
    "school", "church", "hospital", "store"
]

# ─────────────────────────────────────────────────────────────
# GOOGLE PLACES API CALLS
# ─────────────────────────────────────────────────────────────

def search_places(query: str) -> list:
    """
    Calls Google Places Text Search API.
    Returns list of raw place results.
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    results = []
    params = {"query": query, "key": GOOGLE_API_KEY}

    while True:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"  API error: {data.get('status')} — {query}")
            break

        results.extend(data.get("results", []))
        next_token = data.get("next_page_token")

        if not next_token:
            break

        # Google requires a short wait before next_page_token is valid
        time.sleep(3)
        params = {"pagetoken": next_token, "key": GOOGLE_API_KEY}

    return results


def get_place_details(place_id: str) -> dict:
    """
    Fetches detailed info for a single place.
    Gets website, phone, opening hours, address.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,"
                  "website,rating,user_ratings_total,"
                  "types,url",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("result", {})


# ─────────────────────────────────────────────────────────────
# DATA PROCESSING
# ─────────────────────────────────────────────────────────────

def is_relevant(place: dict, category: str) -> bool:
    """
    Filters out irrelevant Places results.
    Google returns noise — hotels, pubs, schools etc.
    """
    types = place.get("types", [])
    for excluded in EXCLUDED_TYPES:
        if excluded in types:
            return False
    return True


def map_to_vendor(place: dict, details: dict, category: str) -> dict:
    """
    Maps raw Google Places data to our vendor schema.
    Only populates fields we can reliably extract from Places API.
    """
    return {
        "id":            str(uuid.uuid4()),
        "name":          place.get("name", ""),
        "category":      category,
        "subcategory":   None,
        "city":          CITY,
        "country":       "GB",
        "address":       details.get("formatted_address", ""),
        "capacity_min":  None,           # not available from Places API
        "capacity_max":  None,           # requires website scraping (future)
        "price_from":    None,           # not available from Places API
        "price_unit":    None,
        "currency":      "GBP",
        "email":         None,           # not available from Places API
        "phone":         details.get("formatted_phone_number", ""),
        "website":       details.get("website", ""),
        "contact_form":  None,
        "description":   None,
        "amenities":     None,
        "tags":          None,
        "source":        "google_places",
        "source_url":    details.get("url", ""),
        "rating_external": place.get("rating"),
        "rating_count":  place.get("user_ratings_total"),
        "verified":      0,
        "last_verified": str(date.today()),
    }


# ─────────────────────────────────────────────────────────────
# DATABASE INSERTION
# ─────────────────────────────────────────────────────────────

def insert_vendor(conn: sqlite3.Connection, vendor: dict) -> bool:
    """
    Inserts a vendor into vendors table.
    Skips duplicates based on name + city match.
    Returns True if inserted, False if skipped.
    """
    cursor = conn.cursor()

    # Deduplicate by name + city
    cursor.execute(
        "SELECT id FROM vendors WHERE name = ? AND city = ?",
        (vendor["name"], vendor["city"])
    )
    if cursor.fetchone():
        return False

    cursor.execute("""
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
    conn.commit()
    return True


# ─────────────────────────────────────────────────────────────
# EXPERIMENT LOGGING
# Writes result directly to experiments table
# ─────────────────────────────────────────────────────────────

def log_experiment(conn: sqlite3.Connection, results: dict):
    """
    Logs A1 experiment outcome to experiments table.
    Maps directly to validation board entry.
    """
    total     = results["total_inserted"]
    validated = total >= 200

    conn.execute("""
        INSERT INTO experiments (
            id, assumption_id, hypothesis, method,
            min_success, result, outcome, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        "A1",
        "≥200 SME-relevant vendors per city accessible via Google Places API",
        f"Google Places Text Search across {len(SEARCH_QUERIES)} categories, "
        f"{sum(len(v) for v in SEARCH_QUERIES.values())} queries, city: {CITY}",
        "≥200 unique vendors inserted into vendors table",
        json.dumps(results),
        "validated" if validated else "invalidated",
        f"Total unique vendors found: {total}. "
        f"Threshold: 200. "
        f"Result: {'PASS' if validated else 'FAIL'}"
    ))
    conn.commit()


# ─────────────────────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────────────────────

def run(city: str = CITY):
    """
    Main entry point. Runs all queries, inserts vendors, logs experiment.
    Call with different city to collect vendors for any market.
    """
    print(f"\n{'='*55}")
    print(f"  A1 Experiment — Vendor API Collection")
    print(f"  City: {city}")
    print(f"{'='*55}\n")

    conn = sqlite3.connect(DB_PATH)
    all_raw = []
    results_by_category = {}

    for category, queries in SEARCH_QUERIES.items():
        print(f"Category: {category.upper()}")
        inserted    = 0
        found_total = 0
        seen_ids    = set()

        for query in queries:
            print(f"  Searching: '{query}'")
            places = search_places(query)

            for place in places:
                place_id = place.get("place_id")

                # Skip duplicates within this run
                if place_id in seen_ids:
                    continue
                seen_ids.add(place_id)

                if not is_relevant(place, category):
                    continue

                found_total += 1

                # Get full details (website, phone etc.)
                details = get_place_details(place_id)
                time.sleep(0.1)   # respectful rate limiting

                vendor = map_to_vendor(place, details, category)
                all_raw.append({"place": place, "details": details})

                if insert_vendor(conn, vendor):
                    inserted += 1

        results_by_category[category] = {
            "found":    found_total,
            "inserted": inserted
        }
        print(f"  → Found: {found_total} | Inserted (unique): {inserted}\n")

    # Save raw JSON for audit trail
    os.makedirs(os.path.dirname(RAW_OUTPUT), exist_ok=True)
    with open(RAW_OUTPUT, "w") as f:
        json.dump(all_raw, f, indent=2)
    print(f"Raw data saved to {RAW_OUTPUT}")

    # Summary
    total_inserted = sum(r["inserted"] for r in results_by_category.values())
    results = {
        "city":                 city,
        "total_inserted":       total_inserted,
        "by_category":          results_by_category,
        "queries_run":          sum(len(v) for v in SEARCH_QUERIES.values()),
        "threshold":            200,
        "validated":            total_inserted >= 200
    }

    print(f"\n{'='*55}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*55}")
    for cat, r in results_by_category.items():
        print(f"  {cat:<12} found: {r['found']:<5} inserted: {r['inserted']}")
    print(f"  {'─'*40}")
    print(f"  TOTAL INSERTED: {total_inserted}")
    print(f"  THRESHOLD:      200")
    print(f"  OUTCOME:        {'VALIDATED' if results['validated'] else 'INVALIDATED'}")
    print(f"{'='*55}\n")

    log_experiment(conn, results)
    conn.close()

    return results


if __name__ == "__main__":
    run()