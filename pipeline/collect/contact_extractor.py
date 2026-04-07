# pipeline/collect/contact_extractor.py
# ─────────────────────────────────────────────────────────────
# Extracts contact information from vendor websites
# Tests A2: contact info reachable at scale without manual work
# ─────────────────────────────────────────────────────────────

import re
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

DB_PATH = "data/vendors.db"

# Common contact page paths to check
CONTACT_PATHS = [
    "/contact", "/contact-us", "/contacts",
    "/get-in-touch", "/enquire", "/enquiries",
    "/about/contact", "/reach-us"
]

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Emails to exclude — generic/irrelevant
EXCLUDED_DOMAINS = [
    "sentry.io", "example.com", "google.com",
    "wixpress.com", "squarespace.com"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OffsiteFlow/1.0; contact research)"
}


# ─────────────────────────────────────────────────────────────
# EXTRACTION LOGIC
# ─────────────────────────────────────────────────────────────

def fetch_page(url: str, timeout: int = 8) -> str | None:
    """Fetches a page and returns HTML text. Returns None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        if response.status_code == 200:
            return response.text
    except Exception:
        pass
    return None


EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,4}"
)

def clean_email(raw: str) -> str | None:
    """
    Cleans a raw extracted email string.
    Removes leading digits, trailing garbage, validates format.
    """
    # Strip leading numbers (phone prefixes like "4025info@...")
    email = re.sub(r"^\d+", "", raw)

    # Extract just the valid email portion — stops at TLD boundary
    match = re.match(
        r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,4})", email
    )
    if not match:
        return None

    email = match.group(1).lower().strip()

    # Sanity checks
    if len(email) > 100:       return None
    if email.count("@") != 1:  return None
    if ".." in email:          return None

    return email


def extract_emails_from_html(html: str) -> list:
    """
    Extracts clean email addresses from raw HTML.
    Prioritises mailto: links over text parsing.
    """
    soup   = BeautifulSoup(html, "html.parser")
    found  = []

    # Priority 1 — mailto: links (always cleanest)
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("mailto:"):
            raw   = href.replace("mailto:", "").split("?")[0].strip()
            email = clean_email(raw)
            if email and email not in found:
                found.append(email)

    # Priority 2 — regex on page text (fallback)
    if not found:
        text = soup.get_text()
        for raw in EMAIL_REGEX.findall(text):
            email = clean_email(raw)
            if email and email not in found:
                domain = email.split("@")[-1]
                if domain not in EXCLUDED_DOMAINS:
                    found.append(email)

    return found


def find_contact_email(website: str) -> tuple[str | None, str | None]:
    """
    Attempts to find a contact email for a vendor website.
    Checks homepage first, then common contact page paths.
    Returns (email, source_url) or (None, None)
    """
    if not website:
        return None, None

    # Normalise URL
    if not website.startswith("http"):
        website = "https://" + website

    # Try homepage first
    html = fetch_page(website)
    if html:
        emails = extract_emails_from_html(html)
        if emails:
            return emails[0], website

    # Try common contact page paths
    for path in CONTACT_PATHS:
        contact_url = urljoin(website, path)
        html = fetch_page(contact_url)
        if html:
            emails = extract_emails_from_html(html)
            if emails:
                return emails[0], contact_url
        time.sleep(0.5)

    return None, None


# ─────────────────────────────────────────────────────────────
# DATABASE OPERATIONS
# ─────────────────────────────────────────────────────────────

def get_vendors_without_email(conn: sqlite3.Connection) -> list:
    """Returns vendors that have a website but no email yet."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, website 
        FROM vendors 
        WHERE (email IS NULL OR email = '')
        AND (website IS NOT NULL AND website != '')
        ORDER BY category
    """)
    return cursor.fetchall()


def update_vendor_email(conn: sqlite3.Connection, vendor_id: str,
                        email: str, source_url: str):
    """Updates a vendor record with extracted email."""
    conn.execute("""
        UPDATE vendors 
        SET email        = ?,
            source_url   = ?,
            updated_at   = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (email, source_url, vendor_id))
    conn.commit()


# ─────────────────────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────────────────────

def run(limit: int = None) -> dict:
    """
    Scrapes vendor websites to extract contact emails.
    limit: max vendors to process (None = all)
    """
    conn    = sqlite3.connect(DB_PATH)
    vendors = get_vendors_without_email(conn)

    if limit:
        vendors = vendors[:limit]

    total       = len(vendors)
    found       = 0
    not_found   = 0
    no_website  = 0

    print(f"\n{'='*55}")
    print(f"  A2 Experiment — Contact Reachability")
    print(f"  Processing {total} vendors without email")
    print(f"{'='*55}\n")

    for i, (vendor_id, name, website) in enumerate(vendors, 1):
        print(f"[{i}/{total}] {name[:40]:<40}", end=" ")

        if not website:
            print("— no website")
            no_website += 1
            continue

        email, source_url = find_contact_email(website)

        if email:
            update_vendor_email(conn, vendor_id, email, source_url)
            print(f"✓ {email}")
            found += 1
        else:
            print("✗ no email found")
            not_found += 1

        time.sleep(0.5)  # respectful rate limiting

    # Results
    reachable_pct = round((found / total) * 100, 1) if total > 0 else 0
    validated     = reachable_pct >= 60

    results = {
        "total_processed":  total,
        "emails_found":     found,
        "not_found":        not_found,
        "no_website":       no_website,
        "reachable_pct":    reachable_pct,
        "threshold":        60,
        "validated":        validated
    }

    print(f"\n{'='*55}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*55}")
    print(f"  Processed:      {total}")
    print(f"  Emails found:   {found} ({reachable_pct}%)")
    print(f"  Not found:      {not_found}")
    print(f"  No website:     {no_website}")
    print(f"  Threshold:      60%")
    print(f"  OUTCOME:        {'VALIDATED' if validated else 'INVALIDATED'}")
    print(f"{'='*55}\n")

    # Log to experiments table
    import json, uuid
    conn.execute("""
        INSERT INTO experiments (
            id, assumption_id, hypothesis, method,
            min_success, result, outcome, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        "A2",
        "≥60% of scraped vendors have a publicly extractable email address",
        f"Automated website scraping of {total} vendor homepages and contact pages",
        "≥60% email extraction rate",
        json.dumps(results),
        "validated" if validated else "invalidated",
        f"Email found for {found}/{total} vendors ({reachable_pct}%)"
    ))
    conn.commit()
    conn.close()

    return results