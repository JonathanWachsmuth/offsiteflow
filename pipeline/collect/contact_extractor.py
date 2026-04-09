# pipeline/collect/contact_extractor.py
# ─────────────────────────────────────────────────────────────
# Extracts contact emails from vendor websites.
# Tests A2: contact info reachable at scale without manual work.
# ─────────────────────────────────────────────────────────────

import re
import time
import json
import uuid
import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config.settings import A2_MIN_EMAIL_RATE
from db.connection import get_db

logger = logging.getLogger(__name__)

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contacts",
    "/get-in-touch", "/enquire", "/enquiries",
    "/about/contact", "/reach-us"
]

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,4}"
)

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
    """Fetches a page and returns HTML. Returns None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        if response.status_code == 200:
            return response.text
    except Exception as exc:
        logger.debug("Fetch failed for %s: %s", url, exc)
    return None


def clean_email(raw: str) -> str | None:
    """Cleans a raw email string. Returns None if invalid."""
    email = re.sub(r"^\d+", "", raw)
    match = re.match(
        r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,4})", email
    )
    if not match:
        return None

    email = match.group(1).lower().strip()

    if len(email) > 100:       return None
    if email.count("@") != 1:  return None
    if ".." in email:          return None

    return email


def extract_emails_from_html(html: str) -> list:
    """
    Extracts email addresses from HTML.
    Prioritises mailto: links over text regex.
    """
    soup  = BeautifulSoup(html, "html.parser")
    found = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("mailto:"):
            raw   = href.replace("mailto:", "").split("?")[0].strip()
            email = clean_email(raw)
            if email and email not in found:
                found.append(email)

    if not found:
        text = soup.get_text()
        for raw in EMAIL_REGEX.findall(text):
            email  = clean_email(raw)
            domain = email.split("@")[-1] if email else ""
            if email and domain not in EXCLUDED_DOMAINS and email not in found:
                found.append(email)

    return found


def find_contact_email(website: str) -> tuple[str | None, str | None]:
    """
    Finds a contact email for a vendor website.
    Checks homepage first, then common contact page paths.
    Returns (email, source_url) or (None, None).
    """
    if not website:
        return None, None

    if not website.startswith("http"):
        website = "https://" + website

    html = fetch_page(website)
    if html:
        emails = extract_emails_from_html(html)
        if emails:
            return emails[0], website

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
# DATABASE
# ─────────────────────────────────────────────────────────────

def get_vendors_without_email(conn) -> list:
    """Returns vendors that have a website but no email yet."""
    rows = conn.execute("""
        SELECT id, name, website
        FROM vendors
        WHERE (email IS NULL OR email = '')
        AND   (website IS NOT NULL AND website != '')
        ORDER BY category
    """).fetchall()
    return [(r["id"], r["name"], r["website"]) for r in rows]


def update_vendor_email(conn, vendor_id: str, email: str, source_url: str):
    """Updates a vendor record with an extracted email."""
    conn.execute("""
        UPDATE vendors
        SET email      = ?,
            source_url = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (email, source_url, vendor_id))


# ─────────────────────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────────────────────

def run(limit: int = None) -> dict:
    """
    Scrapes vendor websites to extract contact emails.
    limit: max vendors to process (None = all).
    Returns result dict with reachable_pct and validated flag.
    """
    logger.info("Starting A2 contact extraction")

    with get_db() as conn:
        vendors = get_vendors_without_email(conn)

        if limit:
            vendors = vendors[:limit]

        total      = len(vendors)
        found      = 0
        not_found  = 0
        no_website = 0

        logger.info("Processing %d vendors without email", total)

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
                logger.debug("Found email for %s: %s", name, email)
                print(f"✓ {email}")
                found += 1
            else:
                logger.debug("No email found for %s", name)
                print("✗ no email found")
                not_found += 1

            time.sleep(0.5)

        reachable_pct = round((found / total) * 100, 1) if total > 0 else 0
        validated     = reachable_pct >= (A2_MIN_EMAIL_RATE * 100)

        results = {
            "total_processed": total,
            "emails_found":    found,
            "not_found":       not_found,
            "no_website":      no_website,
            "reachable_pct":   reachable_pct,
            "threshold":       A2_MIN_EMAIL_RATE * 100,
            "validated":       validated
        }

        print(f"\n{'='*55}")
        print(f"  RESULTS SUMMARY")
        print(f"{'='*55}")
        print(f"  Processed:    {total}")
        print(f"  Emails found: {found} ({reachable_pct}%)")
        print(f"  Not found:    {not_found}")
        print(f"  No website:   {no_website}")
        print(f"  Threshold:    {A2_MIN_EMAIL_RATE*100:.0f}%")
        print(f"  OUTCOME:      {'VALIDATED' if validated else 'INVALIDATED'}")
        print(f"{'='*55}\n")

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
            f"≥{A2_MIN_EMAIL_RATE*100:.0f}% email extraction rate",
            json.dumps(results),
            "validated" if validated else "invalidated",
            f"Email found for {found}/{total} vendors ({reachable_pct}%)"
        ))

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run(limit=50)
