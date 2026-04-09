# pipeline/extract/quote_parser.py
# ─────────────────────────────────────────────────────────────
# Extracts structured quote data from vendor responses.
# Handles both Tally form JSON and free-text email replies.
# Tests assumption A5: LLM extracts pricing with ≥80% accuracy.
# ─────────────────────────────────────────────────────────────

import json
import uuid
import logging
from datetime import datetime, timezone

import anthropic

from config.settings import ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS
from db.connection import get_db

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────────────────────
# EXTRACTION SCHEMA
# ─────────────────────────────────────────────────────────────

EXTRACTION_SCHEMA = {
    "base_price":         "Total flat price if quoted (number, GBP)",
    "price_per_head":     "Price per person if quoted (number, GBP)",
    "service_fee":        "Service charge percentage or flat fee",
    "vat_rate":           "VAT rate as decimal e.g. 0.20 for 20%",
    "total_estimated":    "Total estimated cost including all fees",
    "capacity_offered":   "Maximum number of people they can accommodate",
    "availability":       "1 if available on requested dates, 0 if not",
    "inclusions":         "List of what is included e.g. [AV, catering, parking]",
    "exclusions":         "List of what is NOT included",
    "price_unit":         "How price is structured: flat / per_head / per_day",
    "currency":           "Currency code e.g. GBP",
    "notes":              "Any important conditions, minimums, or caveats"
}

# Maps Tally form field names to schema field names
TALLY_FIELD_MAP = {
    "maximum_capacity": "capacity_offered",
    "base_price":       "base_price",
    "price_per_head":   "price_per_head",
    "service_fee":      "service_fee",
    "available":        "availability",
    "inclusions":       "inclusions",
    "exclusions":       "exclusions",
    "notes":            "notes",
    "price_unit":       "price_unit",
    "currency":         "currency",
}


# ─────────────────────────────────────────────────────────────
# RESPONSE TYPE DETECTION
# ─────────────────────────────────────────────────────────────

def detect_response_type(raw_response) -> str:
    """Returns 'form' if response is a dict/JSON object, 'email' otherwise."""
    if isinstance(raw_response, dict):
        return "form"
    if isinstance(raw_response, str):
        stripped = raw_response.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                json.loads(stripped)
                return "form"
            except json.JSONDecodeError:
                pass
    return "email"


# ─────────────────────────────────────────────────────────────
# FORM EXTRACTOR (Tally responses)
# ─────────────────────────────────────────────────────────────

def map_tally_response(form_data: dict) -> tuple[dict, dict, str]:
    """
    Maps Tally form fields directly to extraction schema.
    Returns (extracted, confidence, notes). All confidence scores = 1.0
    since form data is unambiguous.
    """
    extracted  = {}
    confidence = {}
    notes      = "Tally form response — high confidence extraction"

    for tally_field, schema_field in TALLY_FIELD_MAP.items():
        value = form_data.get(tally_field)
        if value is None or value == "":
            continue

        if schema_field == "availability":
            if isinstance(value, str):
                extracted[schema_field] = 1 if value.lower() in ("yes", "true", "1") else 0
            else:
                extracted[schema_field] = int(bool(value))
            confidence[schema_field] = 1.0
            continue

        if schema_field in ("inclusions", "exclusions"):
            if isinstance(value, list):
                extracted[schema_field] = value
            else:
                extracted[schema_field] = [
                    item.strip() for item in str(value).split(",") if item.strip()
                ]
            confidence[schema_field] = 1.0
            continue

        if schema_field == "vat_rate" and isinstance(value, (int, float)):
            extracted[schema_field] = value / 100 if value > 1 else value
            confidence[schema_field] = 1.0
            continue

        extracted[schema_field]  = value
        confidence[schema_field] = 1.0

    extracted["currency"]  = form_data.get("currency", "GBP")
    confidence["currency"] = 1.0

    return extracted, confidence, notes


# ─────────────────────────────────────────────────────────────
# EMAIL EXTRACTOR (LLM)
# ─────────────────────────────────────────────────────────────

def extract_from_text(raw_response: str, vendor_name: str,
                      category: str, brief: dict) -> dict:
    """
    Uses LLM to extract structured quote data from free-text email.
    Returns dict with 'extracted', 'confidence', 'extraction_notes'.
    Raises on LLM or JSON failure.
    """
    schema_description = "\n".join(
        f"  - {field}: {desc}" for field, desc in EXTRACTION_SCHEMA.items()
    )

    prompt = f"""
You are extracting structured pricing data from a vendor quote
response for a corporate event planning platform.

VENDOR: {vendor_name} ({category})

EVENT CONTEXT:
- Headcount:  {brief.get('headcount', 'unknown')} people
- Budget:     £{brief.get('budget_total', 'unknown')}
- Date:       {brief.get('date_start', 'unknown')}
- City:       {brief.get('city', 'London')}

RAW VENDOR RESPONSE:
\"\"\"
{raw_response}
\"\"\"

Extract the following fields:
{schema_description}

Rules:
- Extract ONLY information explicitly stated in the response
- Do not infer or calculate values not directly mentioned
- For inclusions/exclusions use a JSON array of strings
- For unavailable fields use null
- Currency should always be GBP unless explicitly stated otherwise

Confidence scores (0.0-1.0) per field:
- 1.0 = explicitly stated   0.7 = clearly implied
- 0.4 = inferred            0.0 = not found / null

Return ONLY valid JSON, no markdown:
{{
    "extracted": {{
        "base_price": null, "price_per_head": null, "service_fee": null,
        "vat_rate": null, "total_estimated": null, "capacity_offered": null,
        "availability": null, "inclusions": null, "exclusions": null,
        "price_unit": null, "currency": "GBP", "notes": null
    }},
    "confidence": {{
        "base_price": 0.0, "price_per_head": 0.0, "service_fee": 0.0,
        "vat_rate": 0.0, "total_estimated": 0.0, "capacity_offered": 0.0,
        "availability": 0.0, "inclusions": 0.0, "exclusions": 0.0,
        "price_unit": 0.0, "currency": 1.0, "notes": 0.0
    }},
    "extraction_notes": "brief note on quality or gaps"
}}
"""

    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    except json.JSONDecodeError as exc:
        logger.error("LLM extraction returned invalid JSON for %s: %s", vendor_name, exc)
        raise ValueError(f"LLM extraction JSON error for {vendor_name}: {exc}") from exc
    except Exception as exc:
        logger.error("LLM extraction failed for %s: %s", vendor_name, exc)
        raise


# ─────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────

def validate_extraction(extracted: dict, confidence: dict, brief: dict) -> dict:
    """
    Validates extracted values. Adjusts confidence for suspicious values.
    Returns dict with 'warnings' and updated 'confidence'.
    """
    warnings  = []
    budget    = brief.get("budget_total")
    headcount = brief.get("headcount")

    base  = extracted.get("base_price")
    ph    = extracted.get("price_per_head")
    total = extracted.get("total_estimated")

    if base and budget and base > budget * 2:
        warnings.append(f"base_price £{base} is >2x the event budget £{budget}")
        confidence["base_price"] = confidence.get("base_price", 1.0) * 0.5

    if ph and headcount and total:
        implied = ph * headcount
        if abs(implied - total) > total * 0.3:
            warnings.append(
                f"price_per_head × headcount (£{implied:.0f}) "
                f"doesn't match total_estimated (£{total:.0f})"
            )

    if ph and ph > 2000:
        warnings.append(f"price_per_head £{ph} seems unusually high")
        confidence["price_per_head"] = confidence.get("price_per_head", 1.0) * 0.6

    avail = extracted.get("availability")
    if avail not in (0, 1, None):
        extracted["availability"] = 1 if avail else 0

    vat = extracted.get("vat_rate")
    if vat and vat > 1:
        extracted["vat_rate"] = vat / 100
        warnings.append(f"vat_rate converted from {vat}% to {vat/100}")

    for w in warnings:
        logger.warning("Extraction warning: %s", w)

    return {"warnings": warnings, "confidence": confidence}


# ─────────────────────────────────────────────────────────────
# CONFIDENCE SCORER
# ─────────────────────────────────────────────────────────────

def score_extraction(extracted: dict, confidence: dict) -> float:
    """Produces an overall extraction quality score (0.0–1.0)."""
    weights = {
        "base_price":       0.20,
        "price_per_head":   0.20,
        "total_estimated":  0.15,
        "availability":     0.15,
        "inclusions":       0.10,
        "capacity_offered": 0.10,
        "price_unit":       0.05,
        "service_fee":      0.03,
        "vat_rate":         0.02,
    }
    score = sum(
        weight * confidence.get(field, 0.0)
        for field, weight in weights.items()
        if extracted.get(field) is not None
    )
    return round(score, 3)


# ─────────────────────────────────────────────────────────────
# DATABASE WRITE
# ─────────────────────────────────────────────────────────────

def save_quote(conn, outreach_id: str, event_id: str, vendor_id: str,
               extracted: dict, confidence_score: float,
               extraction_notes: str) -> str:
    """Saves extracted quote to quotes table. Returns quote_id."""
    quote_id = str(uuid.uuid4())

    conn.execute("""
        INSERT INTO quotes (
            id, outreach_id, event_id, vendor_id,
            base_price, price_per_head, service_fee,
            vat_rate, total_estimated, currency, price_unit,
            inclusions, exclusions, capacity_offered,
            availability, confidence_score, extraction_notes,
            extracted_at, normalised, status
        ) VALUES (
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?
        )
    """, (
        quote_id, outreach_id, event_id, vendor_id,
        extracted.get("base_price"),
        extracted.get("price_per_head"),
        extracted.get("service_fee"),
        extracted.get("vat_rate"),
        extracted.get("total_estimated"),
        extracted.get("currency", "GBP"),
        extracted.get("price_unit"),
        json.dumps(extracted.get("inclusions") or []),
        json.dumps(extracted.get("exclusions") or []),
        extracted.get("capacity_offered"),
        extracted.get("availability"),
        confidence_score,
        extraction_notes,
        datetime.now(timezone.utc).isoformat(),
        0,
        "extracted"
    ))
    return quote_id


# ─────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────

def parse_quote(raw_response, vendor: dict, brief: dict,
                outreach_id: str, event_id: str,
                save_to_db: bool = True) -> dict:
    """
    Full extraction pipeline for one vendor response.
    Handles both Tally form JSON and free-text email replies.

    Args:
        raw_response: dict (Tally form) or str (email text)
        vendor:       vendor dict with id, name, category
        brief:        event brief dict
        outreach_id:  links back to outreach table
        event_id:     links back to events table
        save_to_db:   set False for testing / experiments

    Returns:
        quote_id, extracted, confidence_score,
        warnings, extraction_notes, response_type
    """
    vendor_id   = vendor["id"]
    vendor_name = vendor.get("name", "Unknown")
    category    = vendor.get("category", "venue")

    response_type = detect_response_type(raw_response)
    logger.info("Parsing %s response from %s", response_type, vendor_name)

    if response_type == "form":
        form_data = raw_response if isinstance(raw_response, dict) \
                    else json.loads(raw_response)
        extracted, confidence, extraction_notes = map_tally_response(form_data)
    else:
        result           = extract_from_text(raw_response, vendor_name, category, brief)
        extracted        = result["extracted"]
        confidence       = result["confidence"]
        extraction_notes = result.get("extraction_notes", "")

    validation       = validate_extraction(extracted, confidence, brief)
    warnings         = validation["warnings"]
    confidence       = validation["confidence"]
    confidence_score = score_extraction(extracted, confidence)

    logger.info(
        "%s — type: %s, confidence: %.3f, availability: %s, price: %s",
        vendor_name, response_type, confidence_score,
        extracted.get("availability"),
        extracted.get("base_price") or extracted.get("price_per_head")
    )

    quote_id = None
    if save_to_db:
        try:
            with get_db() as conn:
                quote_id = save_quote(
                    conn, outreach_id, event_id, vendor_id,
                    extracted, confidence_score, extraction_notes
                )
            logger.info("Quote saved: %s", quote_id)
        except Exception as exc:
            logger.error("Failed to save quote for %s: %s", vendor_name, exc)

    return {
        "quote_id":         quote_id,
        "extracted":        extracted,
        "confidence_score": confidence_score,
        "warnings":         warnings,
        "extraction_notes": extraction_notes,
        "response_type":    response_type
    }
