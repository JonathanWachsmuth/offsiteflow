# pipeline/outreach/email_sender.py
# ─────────────────────────────────────────────────────────────
# Sends RFQ emails via Gmail SMTP
# Logs every send to outreach table in vendors.db
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import uuid
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

DB_PATH       = "data/vendors.db"
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_EMAIL    = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


# ─────────────────────────────────────────────────────────────
# SMTP CONNECTION
# ─────────────────────────────────────────────────────────────

def get_smtp_connection():
    """Creates and returns an authenticated SMTP connection."""
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASSWORD)
    return server


# ─────────────────────────────────────────────────────────────
# EMAIL BUILDER
# ─────────────────────────────────────────────────────────────

def build_mime_email(rfq: dict,
                     override_to: str = None) -> MIMEMultipart:
    """
    Builds a MIME email from an RFQ dict.
    override_to: send to this address instead of vendor email
                 (used for test sends)
    """
    msg = MIMEMultipart("alternative")

    msg["Subject"] = rfq["subject"]
    msg["From"]    = f"OffsiteFlow <{SMTP_EMAIL}>"
    msg["To"]      = override_to or rfq["email_to"]

    # Plain text fallback
    plain = MIMEText(rfq["plain_body"], "plain")
    html  = MIMEText(rfq["html_body"],  "html")

    # HTML takes priority — attach plain first, html second
    msg.attach(plain)
    msg.attach(html)

    return msg


# ─────────────────────────────────────────────────────────────
# DATABASE LOGGING
# ─────────────────────────────────────────────────────────────

def log_outreach(conn: sqlite3.Connection,
                 rfq: dict,
                 event_id: str,
                 status: str,
                 error: str = None) -> str:
    """
    Logs an outreach attempt to the outreach table.
    Returns the outreach_id.
    """
    outreach_id = str(uuid.uuid4())

    conn.execute("""
        INSERT INTO outreach (
            id, event_id, vendor_id,
            email_to, email_subject, email_body,
            sent_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        outreach_id,
        event_id,
        rfq["vendor_id"],
        rfq["email_to"],
        rfq["subject"],
        rfq["plain_body"],
        datetime.utcnow().isoformat() if status == "sent" else None,
        status
    ))
    conn.commit()
    return outreach_id


# ─────────────────────────────────────────────────────────────
# SEND FUNCTIONS
# ─────────────────────────────────────────────────────────────

def send_single(rfq: dict,
                event_id: str,
                override_to: str = None,
                dry_run: bool = False) -> dict:
    """
    Sends a single RFQ email.

    override_to: redirect to this email (for testing)
    dry_run:     log but do not actually send

    Returns result dict with status and outreach_id.
    """
    conn   = sqlite3.connect(DB_PATH)
    target = override_to or rfq["email_to"]

    print(f"  {'[DRY RUN] ' if dry_run else ''}"
          f"Sending to {rfq['vendor_name']} "
          f"<{target}>...", end=" ")

    if dry_run:
        outreach_id = log_outreach(conn, rfq, event_id, "pending")
        conn.close()
        print("logged (dry run)")
        return {
            "status":      "dry_run",
            "outreach_id": outreach_id,
            "vendor":      rfq["vendor_name"],
            "email_to":    target
        }

    try:
        msg    = build_mime_email(rfq, override_to=override_to)
        server = get_smtp_connection()
        server.sendmail(SMTP_EMAIL, target, msg.as_string())
        server.quit()

        outreach_id = log_outreach(conn, rfq, event_id, "sent")
        conn.close()
        print("✓ sent")

        return {
            "status":      "sent",
            "outreach_id": outreach_id,
            "vendor":      rfq["vendor_name"],
            "email_to":    target
        }

    except Exception as e:
        outreach_id = log_outreach(conn, rfq, event_id,
                                   "failed", str(e))
        conn.close()
        print(f"✗ failed: {e}")

        return {
            "status":      "failed",
            "outreach_id": outreach_id,
            "vendor":      rfq["vendor_name"],
            "error":       str(e)
        }


def send_batch(rfqs: list,
               event_id: str,
               override_to: str = None,
               dry_run: bool = False) -> dict:
    """
    Sends a batch of RFQ emails.
    Returns summary of results.
    """
    print(f"\n{'='*55}")
    print(f"  Email Sender — {'DRY RUN' if dry_run else 'LIVE SEND'}")
    print(f"  Sending {len(rfqs)} emails")
    if override_to:
        print(f"  Redirected to: {override_to}")
    print(f"{'='*55}\n")

    results  = []
    sent     = 0
    failed   = 0

    for rfq in rfqs:
        result = send_single(
            rfq,
            event_id,
            override_to = override_to,
            dry_run     = dry_run
        )
        results.append(result)

        if result["status"] == "sent":
            sent += 1
        elif result["status"] == "failed":
            failed += 1

    print(f"\n{'='*55}")
    print(f"  SEND COMPLETE")
    print(f"  Sent:    {sent}")
    print(f"  Failed:  {failed}")
    print(f"  Dry run: {len(rfqs) - sent - failed}")
    print(f"{'='*55}\n")

    return {
        "total":   len(rfqs),
        "sent":    sent,
        "failed":  failed,
        "results": results
    }


# ─────────────────────────────────────────────────────────────
# TEST SEND
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    from pipeline.outreach.rfq_generator import generate_rfq

    print("Sending test email to jonathan.a.wachsmuth@gmail.com...")

    test_vendor = {
        "id":          "test_vendor_001",
        "name":        "The Venue London",
        "category":    "venue",
        "email":       "test@vendor.com",
        "description": "A stunning riverside venue with outdoor terraces "
                       "perfect for corporate events and team offsites."
    }

    test_brief = {
        "event_type":   "offsite",
        "city":         "London",
        "headcount":    45,
        "budget_total": 15000,
        "date_start":   "2026-06-15",
        "requirements": "outdoor space, countryside feel, team building"
    }

    rfq = generate_rfq(test_vendor, test_brief, "evt_test_001")

    if rfq:
        result = send_single(
            rfq,
            event_id    = "evt_test_001",
            override_to = "jonathan.a.wachsmuth@gmail.com",
            dry_run     = False
        )
        print(f"\nResult: {result['status']}")
    else:
        print("RFQ generation failed")