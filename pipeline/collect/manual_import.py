# pipeline/collect/manual_import.py
# ─────────────────────────────────────────────────────────────
# Loads manually curated vendor CSV into vendors.db.
# Upsert pattern: insert new vendors, enrich existing ones
# (API-collected vendors get enriched with manual contact data).
# ─────────────────────────────────────────────────────────────

import csv
import uuid
import logging
from datetime import date

from config.settings import MANUAL_CSV_PATH
from db.connection import get_db

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["name", "category", "city", "email", "website"]

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

def load_csv(path: str = None) -> list[dict]:
    """
    Loads and validates the vendor CSV.
    Raises FileNotFoundError / ValueError on bad input.
    """
    import os
    csv_path = path or MANUAL_CSV_PATH

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"CSV not found at {csv_path}\n"
            "Save your vendor CSV to data/raw/manual/vendors_seed.csv"
        )

    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"CSV missing required columns: {missing}\n"
                f"Found: {list(reader.fieldnames)}"
            )

        for i, row in enumerate(reader, 1):
            cleaned = {k: v.strip() if v else None for k, v in row.items()}
            if not cleaned.get("name"):
                logger.warning("Row %d skipped — no name", i)
                continue
            rows.append(cleaned)

    logger.info("Loaded %d rows from %s", len(rows), csv_path)
    return rows


# ─────────────────────────────────────────────────────────────
# UPSERT LOGIC
# ─────────────────────────────────────────────────────────────

def find_existing(conn, name: str, city: str) -> str | None:
    """Returns existing vendor id by name + city, or None."""
    row = conn.execute(
        "SELECT id FROM vendors WHERE LOWER(name) = LOWER(?) AND LOWER(city) = LOWER(?)",
        (name.strip(), city.strip())
    ).fetchone()
    return row["id"] if row else None


def insert_vendor(conn, row: dict) -> str:
    """Inserts a new vendor from CSV row. Returns the new vendor id."""
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
        "verified":      1,
        "last_verified": str(date.today())
    })
    return vendor_id


def enrich_vendor(conn, vendor_id: str, row: dict):
    """
    Enriches an existing (API-collected) vendor with manual data.
    Only fills fields that are currently empty — manual data wins.
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

def run(csv_path: str = None) -> dict:
    """
    Loads CSV and upserts vendors into the database.
    Returns summary dict with inserted/enriched counts.
    """
    logger.info("Starting manual vendor import")

    print(f"\n{'='*55}")
    print(f"  Manual Import — Loading vendors from CSV")
    print(f"{'='*55}\n")

    rows     = load_csv(csv_path)
    inserted = 0
    enriched = 0

    with get_db() as conn:
        for row in rows:
            name = row.get("name", "")
            city = row.get("city", "London")

            existing_id = find_existing(conn, name, city)

            if existing_id:
                enrich_vendor(conn, existing_id, row)
                enriched += 1
                logger.debug("Enriched: %s", name)
                print(f"  ENRICHED  {name[:45]}")
            else:
                insert_vendor(conn, row)
                inserted += 1
                logger.debug("Inserted: %s", name)
                print(f"  INSERTED  {name[:45]}")

        row_counts = conn.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN email IS NOT NULL AND email != '' THEN 1 ELSE 0 END) as with_email "
            "FROM vendors"
        ).fetchone()

    total_in_db = row_counts["total"]
    with_email  = row_counts["with_email"]

    print(f"\n{'='*55}")
    print(f"  IMPORT COMPLETE")
    print(f"{'='*55}")
    print(f"  Total in CSV:   {len(rows)}")
    print(f"  Inserted (new): {inserted}")
    print(f"  Enriched (API): {enriched}")
    print(f"  {'─'*40}")
    print(f"  Total in DB:    {total_in_db}")
    print(f"  With email:     {with_email}")
    print(f"{'='*55}\n")

    return {
        "total_in_csv": len(rows),
        "inserted":     inserted,
        "enriched":     enriched,
        "total_in_db":  total_in_db,
        "with_email":   with_email,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
