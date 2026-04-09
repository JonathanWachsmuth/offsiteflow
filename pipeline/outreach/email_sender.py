# pipeline/outreach/email_sender.py
# ─────────────────────────────────────────────────────────────
# Sends RFQ emails via Gmail SMTP.
# Logs every send attempt to the outreach table.
# ─────────────────────────────────────────────────────────────

import uuid
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import (
    SMTP_EMAIL, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT
)
from db.connection import get_db

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# SMTP CONNECTION
# ─────────────────────────────────────────────────────────────

def get_smtp_connection() -> smtplib.SMTP:
    """Creates and returns an authenticated SMTP connection. Raises on failure."""
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        server.ehlo()
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        return server
    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "SMTP authentication failed — check SMTP_EMAIL / SMTP_PASSWORD in .env. "
            "Gmail requires an App Password, not your account password. Error: %s", exc
        )
        raise
    except Exception as exc:
        logger.error("SMTP connection failed: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────
# EMAIL BUILDER
# ─────────────────────────────────────────────────────────────

def build_mime_email(rfq: dict, override_to: str = None) -> MIMEMultipart:
    """
    Builds a MIME email from an RFQ dict.
    override_to: redirect to this address instead of vendor email (used for tests).
    """
    msg            = MIMEMultipart("alternative")
    msg["Subject"] = rfq["subject"]
    msg["From"]    = f"OffsiteFlow <{SMTP_EMAIL}>"
    msg["To"]      = override_to or rfq["email_to"]

    msg.attach(MIMEText(rfq["plain_body"], "plain"))
    msg.attach(MIMEText(rfq["html_body"],  "html"))
    return msg


# ─────────────────────────────────────────────────────────────
# DATABASE LOGGING
# ─────────────────────────────────────────────────────────────

def log_outreach(conn, rfq: dict, event_id: str, status: str) -> str:
    """Logs an outreach attempt to the outreach table. Returns outreach_id."""
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
    return outreach_id


# ─────────────────────────────────────────────────────────────
# SEND FUNCTIONS
# ─────────────────────────────────────────────────────────────

def send_single(rfq: dict, event_id: str,
                override_to: str = None,
                dry_run: bool = False) -> dict:
    """
    Sends a single RFQ email.

    override_to: redirect to this address (for testing)
    dry_run:     log but do not actually send

    Returns result dict with status and outreach_id.
    """
    target = override_to or rfq["email_to"]
    label  = "[DRY RUN] " if dry_run else ""
    print(f"  {label}Sending to {rfq['vendor_name']} <{target}>...", end=" ")

    if dry_run:
        with get_db() as conn:
            outreach_id = log_outreach(conn, rfq, event_id, "pending")
        print("logged (dry run)")
        logger.info("Dry run: RFQ logged for %s", rfq["vendor_name"])
        return {
            "status":      "dry_run",
            "outreach_id": outreach_id,
            "vendor":      rfq["vendor_name"],
            "email_to":    target,
        }

    try:
        msg    = build_mime_email(rfq, override_to=override_to)
        server = get_smtp_connection()
        server.sendmail(SMTP_EMAIL, target, msg.as_string())
        server.quit()

        with get_db() as conn:
            outreach_id = log_outreach(conn, rfq, event_id, "sent")

        print("✓ sent")
        logger.info("RFQ sent to %s <%s>", rfq["vendor_name"], target)
        return {
            "status":      "sent",
            "outreach_id": outreach_id,
            "vendor":      rfq["vendor_name"],
            "email_to":    target,
        }

    except Exception as exc:
        with get_db() as conn:
            outreach_id = log_outreach(conn, rfq, event_id, "failed")

        print(f"✗ failed: {exc}")
        logger.error("RFQ failed for %s: %s", rfq["vendor_name"], exc)
        return {
            "status":      "failed",
            "outreach_id": outreach_id,
            "vendor":      rfq["vendor_name"],
            "error":       str(exc),
        }


def send_batch(rfqs: list, event_id: str,
               override_to: str = None,
               dry_run: bool = False) -> dict:
    """Sends a batch of RFQ emails. Returns summary of results."""
    print(f"\n{'='*55}")
    print(f"  Email Sender — {'DRY RUN' if dry_run else 'LIVE SEND'}")
    print(f"  Sending {len(rfqs)} emails")
    if override_to:
        print(f"  Redirected to: {override_to}")
    print(f"{'='*55}\n")

    results = []
    sent    = 0
    failed  = 0

    for rfq in rfqs:
        result = send_single(rfq, event_id, override_to=override_to, dry_run=dry_run)
        results.append(result)
        if result["status"] == "sent":
            sent += 1
        elif result["status"] == "failed":
            failed += 1

    print(f"\n{'='*55}")
    print(f"  SEND COMPLETE — sent: {sent}  failed: {failed}  "
          f"dry run: {len(rfqs) - sent - failed}")
    print(f"{'='*55}\n")

    return {"total": len(rfqs), "sent": sent, "failed": failed, "results": results}
