# db/seed.py
# ─────────────────────────────────────────────────────────────
# Loads manual vendor CSV into vendors.db
# Merges with existing API-collected vendors
# Uses upsert pattern — insert new, enrich existing
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import sqlite3
import uuid
from datetime import date

DB_PATH  = "data/vendors.db"
CSV_PATH = "data/raw/manual/vendors_seed.csv"

# ─────────────────────────────────────────────────────────────
# EXPECTED CSV COLUMNS
# Must match what Cowork produced
# ─────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = [
    "name", "category", "city", "email", "website"
]

OPTIONAL_COLUMNS = [
    "subcategory", "country", "address",
    "capacity_min", "capacity_max",
    "price_from", "price_unit", "currency",
    "phone", "contact_form", "description",
    "amenities", "tags", "source", "source_url"
]


# ─────────────────────────────────────────────────────────────
# CSV LOADING
# ─────────────────────────────────────────────────────────────

def load_csv(path: str) -> list[dict]:
    """
    Loads and validates the vendor CSV.
    Returns list of row dicts with cleaned values.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"CSV not found at {path}\n"
            f"Save your Cowork vendor CSV to data/raw/manual/vendors_seed.csv"
        )

    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Validate required columns exist
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"CSV missing required columns: {missing}\n"
                f"Found columns: {list(reader.fieldnames)}"
            )

        for i, row in enumerate(reader, 1):
            # Clean whitespace from all values
            cleaned = {k: v.strip() if v else None for k, v in row.items()}

            # Skip rows with no name
            if not cleaned.get("name"):
                print(f"  Row {i}: skipped — no name")
                continue

            rows.append(cleaned)

    return rows


# ─────────────────────────────────────────────────────────────
# UPSERT LOGIC
# Insert if new vendor, enrich if already exists from API
# ─────────────────────────────────────────────────────────────

def find_existing(conn: sqlite3.Connection,
                  name: str, city: str) -> str | None:
    """
    Checks if vendor already exists by name + city.
    Returns existing id or None.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM vendors WHERE LOWER(name) = LOWER(?) AND LOWER(city) = LOWER(?)",
        (name.strip(), city.strip())
    )
    row = cursor.fetchone()
    return row[0] if row else None


def insert_vendor(conn: sqlite3.Connection, row: dict) -> str:
    """
    Inserts a new vendor record from CSV row.
    Returns the new vendor id.
    """
    vendor_id = str(uuid.uuid4())

    conn.execute("""
        INSERT INTO vendors (
            id, name, category, subcategory,
            city, country, address,
            capacity_min, capacity_max,
            price_from, price_unit, currency,
            email, phone, website, contact_form,
            description, amenities, tags,
            source, source_url,
            verified, last_verified
        ) VALUES (
            :id, :name, :category, :subcategory,
            :city, :country, :address,
            :capacity_min, :capacity_max,
            :price_from, :price_unit, :currency,
            :email, :phone, :website, :contact_form,
            :description, :amenities, :tags,
            :source, :source_url,
            :verified, :last_verified
        )
    """, {
        "id":            vendor_id,
        "name":          row.get("name"),
        "category":      row.get("category", "venue").lower(),
        "subcategory":   row.get("subcategory"),
        "city":          row.get("city", "London"),
        "country":       row.get("country", "GB"),
        "address":       row.get("address"),
        "capacity_min":  _int(row.get("capacity_min")),
        "capacity_max":  _int(row.get("capacity_max")),
        "price_from":    _float(row.get("price_from")),
        "price_unit":    row.get("price_unit"),
        "currency":      row.get("currency", "GBP"),
        "email":         row.get("email"),
        "phone":         row.get("phone"),
        "website":       row.get("website"),
        "contact_form":  row.get("contact_form"),
        "description":   row.get("description"),
        "amenities":     row.get("amenities"),
        "tags":          row.get("tags"),
        "source":        row.get("source", "manual"),
        "source_url":    row.get("source_url"),
        "verified":      1,              # manually verified
        "last_verified": str(date.today())
    })

    return vendor_id


def enrich_vendor(conn: sqlite3.Connection,
                  vendor_id: str, row: dict):
    """
    Enriches an existing vendor (from API) with manual data.
    Only overwrites fields that are currently empty.
    Manual data always wins — it's higher quality.
    """
    conn.execute("""
        UPDATE vendors SET
            email        = COALESCE(NULLIF(email, ''),        :email),
            phone        = COALESCE(NULLIF(phone, ''),        :phone),
            description  = COALESCE(NULLIF(description, ''), :description),
            capacity_min = COALESCE(capacity_min,             :capacity_min),
            capacity_max = COALESCE(capacity_max,             :capacity_max),
            price_from   = COALESCE(price_from,               :price_from),
            amenities    = COALESCE(NULLIF(amenities, ''),    :amenities),
            tags         = COALESCE(NULLIF(tags, ''),         :tags),
            verified     = 1,
            last_verified = :last_verified,
            updated_at   = CURRENT_TIMESTAMP
        WHERE id = :id
    """, {
        "id":            vendor_id,
        "email":         row.get("email"),
        "phone":         row.get("phone"),
        "description":   row.get("description"),
        "capacity_min":  _int(row.get("capacity_min")),
        "capacity_max":  _int(row.get("capacity_max")),
        "price_from":    _float(row.get("price_from")),
        "amenities":     row.get("amenities"),
        "tags":          row.get("tags"),
        "last_verified": str(date.today())
    })


# ─────────────────────────────────────────────────────────────
# TYPE HELPERS
# ─────────────────────────────────────────────────────────────

def _int(val) -> int | None:
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


def _float(val) -> float | None:
    try:
        if not val:
            return None
        return float(str(val).replace("£", "").replace(",", ""))
    except (ValueError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────────────────────

def run():
    print(f"\n{'='*55}")
    print(f"  Seed — Loading manual vendors into database")
    print(f"{'='*55}\n")

    conn    = sqlite3.connect(DB_PATH)
    rows    = load_csv(CSV_PATH)
    total   = len(rows)

    inserted = 0
    enriched = 0
    skipped  = 0

    for row in rows:
        name = row.get("name", "")
        city = row.get("city", "London")

        existing_id = find_existing(conn, name, city)

        if existing_id:
            # Already in DB from API — enrich with manual data
            enrich_vendor(conn, existing_id, row)
            enriched += 1
            print(f"  ENRICHED  {name[:45]}")
        else:
            # New vendor — insert fresh
            insert_vendor(conn, row)
            inserted += 1
            print(f"  INSERTED  {name[:45]}")

    conn.commit()
    conn.close()

    print(f"\n{'='*55}")
    print(f"  SEED COMPLETE")
    print(f"{'='*55}")
    print(f"  Total in CSV:   {total}")
    print(f"  Inserted (new): {inserted}")
    print(f"  Enriched (API): {enriched}")
    print(f"  Skipped:        {skipped}")
    print(f"  {'─'*40}")

    # Check total vendors now in DB
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
    email_count = conn.execute(
        "SELECT COUNT(*) FROM vendors WHERE email IS NOT NULL AND email != ''"
    ).fetchone()[0]
    conn.close()

    print(f"  Total in DB:    {count}")
    print(f"  With email:     {email_count}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()