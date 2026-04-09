# pipeline/normalise/normaliser.py
# ─────────────────────────────────────────────────────────────
# Normalises extracted quotes into a comparable format.
# Tests assumption A7: offers can be compared apples-to-apples.
# ─────────────────────────────────────────────────────────────

import json
import logging

import anthropic

from config.settings import ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS
from db.connection import get_db

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

STANDARD_COMPONENTS = [
    "venue", "catering", "av_equipment", "staffing",
    "activities", "transport", "accommodation"
]

COMPONENT_KEYWORDS = {
    "venue":         ["venue", "room", "space", "hall", "hire", "facility", "garden", "terrace"],
    "catering":      ["catering", "food", "lunch", "dinner", "breakfast",
                      "pastries", "snacks", "meals", "refreshments", "bbq",
                      "ingredients", "chef", "cooking", "cuisine"],
    "av_equipment":  ["av", "audio", "visual", "projector", "screen",
                      "microphone", "sound", "display", "wifi", "broadband"],
    "staffing":      ["staff", "coordinator", "manager", "facilitator",
                      "host", "team", "crew", "service"],
    "activities":    ["activity", "activities", "team building", "workshop",
                      "cooking", "challenge", "game", "experience", "class"],
    "transport":     ["transport", "coach", "minibus", "transfer",
                      "shuttle", "travel", "pickup"],
    "accommodation": ["accommodation", "hotel", "bedroom", "overnight",
                      "stay", "room", "bed"],
}


# ─────────────────────────────────────────────────────────────
# COMPONENT DETECTION
# ─────────────────────────────────────────────────────────────

def detect_components(inclusions: list, exclusions: list, category: str) -> dict:
    """
    Detects which standard components are included/excluded/unknown.
    Uses keyword matching + category inference.
    """
    components = {c: "unknown" for c in STANDARD_COMPONENTS}

    category_map = {
        "venue":         "venue",
        "catering":      "catering",
        "activity":      "activities",
        "transport":     "transport",
        "accommodation": "accommodation",
    }
    if category in category_map:
        components[category_map[category]] = "included"

    inc_text = " ".join(inclusions or []).lower()
    exc_text = " ".join(exclusions or []).lower()

    for component, keywords in COMPONENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in inc_text:
                components[component] = "included"
                break
            if keyword in exc_text:
                components[component] = "excluded"
                break

    return components


# ─────────────────────────────────────────────────────────────
# PRICE NORMALISATION
# ─────────────────────────────────────────────────────────────

def normalise_price(quote: dict, headcount: int) -> dict:
    """
    Normalises pricing to flat total and per-head figures.
    Applies service charge and VAT if present.
    """
    base       = quote.get("base_price")
    per_head   = quote.get("price_per_head")
    service    = quote.get("service_fee", 0) or 0
    vat        = quote.get("vat_rate", 0.20) or 0.20

    if base:
        total_flat = base
    elif per_head:
        total_flat = per_head * headcount
    elif quote.get("total_estimated"):
        total_flat = quote["total_estimated"]
    else:
        logger.warning("Insufficient pricing data for quote from %s",
                       quote.get("vendor_name", "unknown"))
        return {
            "total_flat":     None,
            "total_per_head": None,
            "total_inc_vat":  None,
            "pricing_notes":  "insufficient pricing data"
        }

    if service > 1:
        total_flat = total_flat * (1 + service / 100)
    elif service > 0:
        total_flat = total_flat * (1 + service)

    total_inc_vat  = total_flat * (1 + vat)
    total_per_head = total_flat / headcount if headcount else None

    return {
        "total_flat":     round(total_flat, 2),
        "total_per_head": round(total_per_head, 2) if total_per_head else None,
        "total_inc_vat":  round(total_inc_vat, 2),
        "pricing_notes":  f"base={'flat' if base else 'per_head'}, "
                          f"vat={vat*100:.0f}%, service={service}%"
    }


# ─────────────────────────────────────────────────────────────
# COMPLETENESS SCORING
# ─────────────────────────────────────────────────────────────

def score_completeness(components: dict) -> float:
    """Scores how complete a quote package is (0.0–1.0)."""
    weights = {
        "venue":         0.30,
        "catering":      0.25,
        "av_equipment":  0.15,
        "staffing":      0.15,
        "activities":    0.10,
        "transport":     0.03,
        "accommodation": 0.02,
    }
    score = sum(
        weight for component, weight in weights.items()
        if components.get(component) == "included"
    )
    return round(score, 3)


# ─────────────────────────────────────────────────────────────
# LLM COMPARABILITY CHECK
# ─────────────────────────────────────────────────────────────

def llm_comparability_check(normalised_quotes: list, brief: dict) -> dict:
    """
    Asks LLM to verify normalised quotes are genuinely comparable.
    Returns comparability report dict.
    """
    summary = [
        {
            "vendor":     q["vendor_name"],
            "category":   q["category"],
            "total_flat": q["normalised"]["total_flat"],
            "per_head":   q["normalised"]["total_per_head"],
            "inc_vat":    q["normalised"]["total_inc_vat"],
            "components": {k: v for k, v in q["components"].items() if v != "unknown"},
            "missing":    q["missing_components"]
        }
        for q in normalised_quotes
    ]

    prompt = f"""
You are reviewing normalised vendor quotes for a corporate event.

EVENT:
- Type:      {brief.get('event_type', 'offsite')}
- Headcount: {brief.get('headcount')} people
- Budget:    £{brief.get('budget_total')}
- City:      {brief.get('city')}

NORMALISED QUOTES:
{json.dumps(summary, indent=2)}

Return ONLY valid JSON:
{{
    "comparable": true/false,
    "issues": ["list any comparability issues"],
    "budget_fit": {{
        "within_budget": ["vendor names within budget"],
        "over_budget":   ["vendor names over budget"]
    }},
    "recommendation": "one sentence on which offers best value"
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
        logger.error("Comparability check returned invalid JSON: %s", exc)
        return {"comparable": None, "issues": [str(exc)]}
    except Exception as exc:
        logger.error("Comparability check failed: %s", exc)
        return {"comparable": None, "issues": [str(exc)]}


# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────

def mark_normalised(conn, quote_id: str, notes: str):
    """Marks a quote as normalised in the database."""
    conn.execute("""
        UPDATE quotes
        SET normalised          = 1,
            normalisation_notes = ?,
            status              = 'normalised'
        WHERE id = ?
    """, (notes, quote_id))


# ─────────────────────────────────────────────────────────────
# MAIN NORMALISER
# ─────────────────────────────────────────────────────────────

def normalise_quotes(quotes: list, brief: dict, save_to_db: bool = True) -> dict:
    """
    Normalises a list of extracted quotes for comparison.

    Each quote dict must have:
        quote_id, vendor_id, vendor_name, category + extraction fields.

    Returns:
        {
            "normalised_quotes": [...],
            "comparability":     {...},
            "summary":           {...}
        }
    """
    headcount = brief.get("headcount", 1)
    logger.info("Normalising %d quotes", len(quotes))
    print(f"\n  Normalising {len(quotes)} quotes...")

    normalised_quotes = []

    for quote in quotes:
        vendor_name = quote.get("vendor_name", "Unknown")
        category    = quote.get("category", "venue")
        logger.debug("Normalising %s", vendor_name)
        print(f"  → {vendor_name}")

        inclusions = quote.get("inclusions") or []
        exclusions = quote.get("exclusions") or []

        if isinstance(inclusions, str):
            try:
                inclusions = json.loads(inclusions)
            except Exception:
                inclusions = [i.strip() for i in inclusions.split(",") if i.strip()]

        if isinstance(exclusions, str):
            try:
                exclusions = json.loads(exclusions)
            except Exception:
                exclusions = [e.strip() for e in exclusions.split(",") if e.strip()]

        price        = normalise_price(quote, headcount)
        components   = detect_components(inclusions, exclusions, category)
        completeness = score_completeness(components)
        missing      = [c for c, status in components.items() if status == "excluded"]

        normalised_quotes.append({
            "quote_id":           quote.get("quote_id"),
            "vendor_id":          quote.get("vendor_id"),
            "vendor_name":        vendor_name,
            "category":           category,
            "normalised":         {**price, "completeness_score": completeness},
            "components":         components,
            "missing_components": missing,
            "inclusions":         inclusions,
            "exclusions":         exclusions,
            "availability":       quote.get("availability"),
            "confidence_score":   quote.get("confidence_score")
        })

        if save_to_db and quote.get("quote_id"):
            try:
                with get_db() as conn:
                    mark_normalised(conn, quote["quote_id"],
                                    price.get("pricing_notes", ""))
            except Exception as exc:
                logger.error("Failed to mark quote %s as normalised: %s",
                             quote["quote_id"], exc)

    logger.info("Running LLM comparability check")
    print(f"\n  Running comparability check...")
    comparability = llm_comparability_check(normalised_quotes, brief)

    valid_totals = [
        q["normalised"]["total_inc_vat"]
        for q in normalised_quotes
        if q["normalised"]["total_inc_vat"]
    ]

    summary = {
        "total_quotes": len(normalised_quotes),
        "with_pricing": len(valid_totals),
        "price_min":    min(valid_totals) if valid_totals else None,
        "price_max":    max(valid_totals) if valid_totals else None,
        "price_range":  round(max(valid_totals) - min(valid_totals), 2)
                        if len(valid_totals) > 1 else 0,
        "budget":       brief.get("budget_total"),
        "within_budget": sum(
            1 for t in valid_totals
            if brief.get("budget_total") and t <= brief["budget_total"]
        )
    }

    return {
        "normalised_quotes": normalised_quotes,
        "comparability":     comparability,
        "summary":           summary
    }
