# pipeline/outreach/rfq_generator.py
# ─────────────────────────────────────────────────────────────
# Generates personalised, branded RFQ emails per vendor.
# Brand colours: #1565C0 blue, #0D0D0D black, #ffffff white.
# ─────────────────────────────────────────────────────────────

import logging
from urllib.parse import urlencode

import anthropic

from config.settings import ANTHROPIC_API_KEY, LLM_MODEL, TALLY_FORM_URL

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ─────────────────────────────────────────────────────────────
# EMAIL BODY GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_email_body(vendor: dict, brief: dict) -> str:
    """
    Uses LLM to write a personalised 3-paragraph RFQ email body.
    Raises on LLM failure.
    """
    prompt = f"""
You are writing a professional RFQ email on behalf of OffsiteFlow,
an AI-powered corporate event planning platform based in London.

Write a short, professional email to this vendor requesting a quote.
Maximum 3 short paragraphs. Warm but professional tone.
Do not use hollow phrases like "I hope this email finds you well."
Do not include a subject line or sign-off — just the body paragraphs.

VENDOR:
- Name:        {vendor.get('name')}
- Category:    {vendor.get('category')}
- Description: {vendor.get('description', '')}

EVENT BRIEF:
- Type:         {brief.get('event_type', 'corporate offsite')}
- City:         {brief.get('city', 'London')}
- Headcount:    {brief.get('headcount', 'approx. 40-50')} people
- Budget:       £{brief.get('budget_total', 'TBC')}
- Date:         {brief.get('date_start', 'June 2026')}
- Requirements: {brief.get('requirements', '')}

Paragraph 1: Introduce OffsiteFlow briefly and why we are contacting them.
Paragraph 2: Describe the event and what we need from this specific vendor.
Paragraph 3: Ask them to complete our short quote form (do not include
             the link — it will be added as a button below this text).

Return ONLY the three paragraphs, nothing else.
"""
    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.error("Failed to generate email body for %s: %s", vendor.get("name"), exc)
        raise


# ─────────────────────────────────────────────────────────────
# FORM URL BUILDER
# ─────────────────────────────────────────────────────────────

def build_form_url(event_id: str, vendor_id: str,
                   vendor_name: str, category: str) -> str:
    """Builds a pre-filled Tally form URL with event + vendor context."""
    params = {
        "event_id":    event_id,
        "vendor_id":   vendor_id,
        "vendor_name": vendor_name,
        "category":    category,
    }
    return f"{TALLY_FORM_URL}?{urlencode(params)}"


# ─────────────────────────────────────────────────────────────
# HTML EMAIL TEMPLATE
# ─────────────────────────────────────────────────────────────

def build_html_email(body_text: str, form_url: str,
                     vendor_name: str, brief: dict) -> str:
    """Renders the branded HTML email from generated body text."""

    paragraphs = "".join(
        f'<p style="margin:0 0 16px;font-size:15px;line-height:1.7;color:#444444;">'
        f'{p.strip()}</p>'
        for p in body_text.split("\n\n") if p.strip()
    )

    def row(label, value):
        return (
            f'<tr>'
            f'<td style="padding:7px 16px 7px 0;font-size:13px;color:#888888;'
            f'white-space:nowrap;vertical-align:top;width:110px;">{label}</td>'
            f'<td style="padding:7px 0;font-size:13px;color:#0D1B3E;'
            f'font-weight:500;vertical-align:top;">{value}</td>'
            f'</tr>'
        )

    summary_rows = (
        row("Event type",  brief.get("event_type", "Corporate offsite").title()) +
        row("Location",    brief.get("city", "London")) +
        row("Headcount",   f"{brief.get('headcount', 'TBC')} people") +
        row("Budget",      f"£{brief.get('budget_total', 'TBC')}") +
        row("Date",        brief.get("date_start", "June 2026"))
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Quote Request — OffsiteFlow</title>
</head>
<body style="margin:0;padding:0;background:#f0f2f7;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#f0f2f7;padding:48px 20px;">
  <tr><td align="center">
    <table width="100%" cellpadding="0" cellspacing="0"
           style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;">

      <!-- HEADER -->
      <tr>
        <td style="background:#0D1B3E;padding:28px 40px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="vertical-align:middle;">
                <span style="font-size:20px;font-weight:600;color:#ffffff;letter-spacing:-0.3px;">
                  OffsiteFlow
                </span>
              </td>
              <td align="right" style="vertical-align:middle;">
                <span style="display:inline-block;background:rgba(21,101,192,0.25);
                             border:1px solid #1565C0;color:#7EB3FF;font-size:11px;
                             font-weight:600;text-transform:uppercase;letter-spacing:1px;
                             padding:4px 12px;border-radius:20px;">
                  Quote Request
                </span>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- GRADIENT DIVIDER -->
      <tr>
        <td style="background:linear-gradient(90deg,#1565C0,#A855F7);
                   height:3px;font-size:0;line-height:0;">&nbsp;</td>
      </tr>

      <!-- BODY -->
      <tr>
        <td style="padding:40px 40px 8px;">
          <p style="margin:0 0 24px;font-size:16px;font-weight:600;color:#0D1B3E;">
            Dear {vendor_name} team,
          </p>
          {paragraphs}
        </td>
      </tr>

      <!-- EVENT SUMMARY BOX -->
      <tr>
        <td style="padding:8px 40px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#f5f7ff;border-radius:8px;border-left:4px solid #1565C0;
                        padding:20px 24px;">
            <tr>
              <td colspan="2" style="padding-bottom:12px;font-size:11px;font-weight:700;
                                     color:#1565C0;text-transform:uppercase;letter-spacing:1.2px;">
                Event summary
              </td>
            </tr>
            {summary_rows}
          </table>
        </td>
      </tr>

      <!-- CTA BUTTON -->
      <tr>
        <td align="center" style="padding:0 40px 44px;">
          <p style="font-size:14px;color:#666666;margin:0 0 20px;text-align:center;">
            Submit your quote using the button below — it takes less than 3 minutes.
          </p>
          <table cellpadding="0" cellspacing="0">
            <tr>
              <td style="border-radius:8px;background:linear-gradient(135deg,#1565C0,#6366F1);">
                <a href="{form_url}"
                   style="display:inline-block;color:#ffffff;font-size:15px;font-weight:600;
                          text-decoration:none;padding:14px 44px;border-radius:8px;
                          letter-spacing:0.2px;">
                  Submit your quote &rarr;
                </a>
              </td>
            </tr>
          </table>
          <p style="font-size:11px;color:#aaaaaa;margin:16px 0 0;text-align:center;">
            Or copy this link:&nbsp;
            <a href="{form_url}" style="color:#1565C0;word-break:break-all;">{form_url}</a>
          </p>
        </td>
      </tr>

      <!-- FOOTER -->
      <tr>
        <td style="background:#0D1B3E;padding:24px 40px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td><span style="font-size:14px;font-weight:600;color:#ffffff;">OffsiteFlow</span></td>
              <td align="right">
                <span style="font-size:12px;color:#6B7FA3;">
                  London, UK &nbsp;·&nbsp;
                  <a href="mailto:hello@offsiteflow.com"
                     style="color:#7EB3FF;text-decoration:none;">hello@offsiteflow.com</a>
                </span>
              </td>
            </tr>
          </table>
          <p style="margin:12px 0 0;font-size:11px;color:#4A5D7A;line-height:1.6;">
            This request was sent via OffsiteFlow — the AI-powered corporate event planning
            platform. Reply directly to this email with any questions.
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────

def generate_rfq(vendor: dict, brief: dict, event_id: str) -> dict | None:
    """
    Generates a complete branded RFQ for one vendor.
    Returns None if vendor has no email.
    """
    email_to = vendor.get("email")
    if not email_to:
        logger.warning("Skipping RFQ for %s — no email", vendor.get("name"))
        return None

    vendor_id   = vendor["id"]
    vendor_name = vendor["name"]
    category    = vendor["category"]

    logger.info("Generating RFQ for %s", vendor_name)
    print(f"  Generating RFQ: {vendor_name}...")

    plain_body = generate_email_body(vendor, brief)
    form_url   = build_form_url(event_id, vendor_id, vendor_name, category)
    html_body  = build_html_email(plain_body, form_url, vendor_name, brief)

    subject = (
        f"Quote request — "
        f"{brief.get('event_type', 'corporate event').title()} "
        f"for {brief.get('headcount', '~50')} people, "
        f"{brief.get('city', 'London')}"
    )

    return {
        "vendor_id":   vendor_id,
        "vendor_name": vendor_name,
        "email_to":    email_to,
        "subject":     subject,
        "html_body":   html_body,
        "plain_body":  plain_body,
        "form_url":    form_url,
    }
