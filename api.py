# api.py
# ─────────────────────────────────────────────────────────────
# OffsiteFlow — FastAPI backend
# Run: uvicorn api:app --reload --port 8000
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.match.llm_router       import route
from pipeline.extract.quote_parser   import parse_quote
from pipeline.normalise.normaliser   import normalise_quotes
from pipeline.normalise.ranker       import rank_quotes
from pipeline.outreach.rfq_generator import generate_email_body, build_form_url
from db.supabase_client              import sb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OffsiteFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# BUDGET ALLOCATION PER CATEGORY
# ─────────────────────────────────────────────────────────────

BUDGET_SHARE = {
    "venue":    0.50,
    "catering": 0.30,
    "activity": 0.25,
    "transport": 0.05,
}


# ─────────────────────────────────────────────────────────────
# PER-VENDOR SYNTHETIC RESPONSE GENERATOR
# Template-based — fast, no LLM call, uses real vendor data.
# Each vendor gets a unique response derived from their actual
# DB record (name, capacity, price_from), so the pipeline
# exercises real data end-to-end.
# ─────────────────────────────────────────────────────────────

def generate_synthetic_response(vendor: dict, brief: dict) -> dict:
    """
    Builds a realistic vendor quote response from actual vendor DB fields.
    Returns the same shape as SYNTHETIC used to: {type, response}.
    Calling code passes response directly to parse_quote().
    """
    category   = vendor.get("category", "venue")
    name       = vendor.get("name", "the team")
    headcount  = int(brief.get("headcount") or 45)
    budget     = float(brief.get("budget_total") or 15000)
    cat_budget = budget * BUDGET_SHARE.get(category, 0.25)
    price_from = vendor.get("price_from")
    cap_max    = int(vendor.get("capacity_max") or headcount + 20)

    if category == "venue":
        flat = int(price_from or round(cat_budget * 0.85, -2))
        return {
            "type": "email",
            "response": (
                f"Thank you for your enquiry about {name}. "
                f"For your group of {headcount}, we can offer exclusive hire at "
                f"£{flat:,} + VAT (20%). "
                f"This includes AV equipment, high-speed WiFi, and a dedicated event coordinator. "
                f"Catering is not included but we work with approved partners. "
                f"We have availability for your requested dates. "
                f"Maximum capacity: {cap_max} guests."
            ),
        }

    elif category == "catering":
        pph = int(price_from or max(40, round(cat_budget / headcount * 0.9)))
        return {
            "type": "form",
            "response": {
                "available":        "Yes",
                "maximum_capacity": cap_max,
                "price_per_head":   pph,
                "inclusions":       "all food, serving staff, crockery, linen",
                "exclusions":       "venue, drinks, bar",
                "notes":            "12.5% service charge. VAT at 20%.",
            },
        }

    elif category == "activity":
        pph = int(price_from or max(30, round(cat_budget / headcount * 0.85)))
        return {
            "type": "email",
            "response": (
                f"Thanks for getting in touch with {name}! "
                f"We can run our team programme for your group of {headcount}. "
                f"Pricing: £{pph} per person for a half-day session. "
                f"Includes all equipment, trained facilitators, and a debrief session. "
                f"Excludes venue, catering, and transport. "
                f"Available on your requested dates. Groups of up to {cap_max} welcome."
            ),
        }

    elif category == "transport":
        ppp = max(6, int(price_from or round(cat_budget / headcount * 0.8)))
        return {
            "type": "email",
            "response": (
                f"Hello from {name}. "
                f"We can arrange coach transfers for your group of {headcount} people. "
                f"Pricing: £{ppp} per person per journey, including driver and fuel. "
                f"Available on request — please confirm pickup times and locations."
            ),
        }

    else:
        pph = int(round(cat_budget / max(headcount, 1) * 0.85))
        return {
            "type": "email",
            "response": (
                f"Thank you for contacting {name}. "
                f"We can accommodate your event for {headcount} people. "
                f"Pricing from £{pph} per person. "
                f"Available for your requested dates."
            ),
        }


# ─────────────────────────────────────────────────────────────
# FAST SYNTHETIC EXTRACTOR
# Reads back the fields we put into generate_synthetic_response
# without calling the LLM — cuts shortlist latency from ~30s to <1s.
# ─────────────────────────────────────────────────────────────

def _extract_synthetic(synth: dict, vendor: dict, brief: dict) -> dict:
    """
    Directly extracts structured quote fields from a synthetic response.
    Returns an `extracted` dict compatible with normalise_quotes().
    """
    cat       = vendor.get("category", "venue")
    headcount = int(brief.get("headcount") or 45)
    raw       = synth["response"]
    rtype     = synth["type"]

    if rtype == "form" and isinstance(raw, dict):
        # Catering / any form-type response
        pph        = raw.get("price_per_head") or 0
        cap        = raw.get("maximum_capacity") or headcount + 20
        incl_str   = raw.get("inclusions", "")
        excl_str   = raw.get("exclusions", "")
        inclusions = [i.strip() for i in incl_str.split(",")] if isinstance(incl_str, str) else list(incl_str or [])
        exclusions = [e.strip() for e in excl_str.split(",")] if isinstance(excl_str, str) else list(excl_str or [])
        return {
            "base_price":       None,
            "price_per_head":   float(pph),
            "total_estimated":  float(pph) * headcount,
            "vat_rate":         0.20,
            "service_fee":      0.125,
            "capacity_offered": cap,
            "availability":     1,
            "inclusions":       inclusions,
            "exclusions":       exclusions,
            "price_unit":       "per_head",
            "currency":         "GBP",
            "notes":            raw.get("notes", ""),
            "_confidence_score": 0.80,
        }

    # Email-type response — parse the price we embedded in the text
    import re
    prices = re.findall(r'£([\d,]+)', str(raw))
    nums   = [int(p.replace(",", "")) for p in prices if p]

    if cat == "venue":
        base = nums[0] if nums else 0
        return {
            "base_price":       float(base),
            "price_per_head":   round(float(base) / headcount, 2) if base else None,
            "total_estimated":  float(base) * 1.20,  # inc VAT
            "vat_rate":         0.20,
            "service_fee":      None,
            "capacity_offered": vendor.get("capacity_max") or headcount + 20,
            "availability":     1,
            "inclusions":       ["AV equipment", "WiFi", "event coordinator"],
            "exclusions":       ["catering", "drinks"],
            "price_unit":       "flat",
            "currency":         "GBP",
            "notes":            "",
            "_confidence_score": 0.75,
        }
    elif cat in ("activity", "transport"):
        pph = nums[0] if nums else 0
        return {
            "base_price":       None,
            "price_per_head":   float(pph),
            "total_estimated":  float(pph) * headcount * 1.20,
            "vat_rate":         0.20,
            "service_fee":      None,
            "capacity_offered": vendor.get("capacity_max") or headcount + 20,
            "availability":     1,
            "inclusions":       ["equipment", "facilitators"] if cat == "activity" else ["driver", "fuel"],
            "exclusions":       ["venue", "catering"],
            "price_unit":       "per_head",
            "currency":         "GBP",
            "notes":            "",
            "_confidence_score": 0.75,
        }
    else:
        pph = nums[0] if nums else 0
        return {
            "base_price":       None,
            "price_per_head":   float(pph),
            "total_estimated":  float(pph) * headcount * 1.20,
            "vat_rate":         0.20,
            "service_fee":      None,
            "capacity_offered": headcount + 20,
            "availability":     1,
            "inclusions":       [],
            "exclusions":       [],
            "price_unit":       "per_head",
            "currency":         "GBP",
            "notes":            "",
            "_confidence_score": 0.60,
        }


# ─────────────────────────────────────────────────────────────
# DB HELPER
# ─────────────────────────────────────────────────────────────

def fetch_vendors_by_ids(vendor_ids: list[str]) -> list[dict]:
    """Fetches full vendor records from Supabase by ID list."""
    if not vendor_ids:
        return []
    result = sb.table("vendors").select("*").in_("id", vendor_ids).execute()
    rows = result.data or []
    # Restore caller's requested order
    order = {vid: i for i, vid in enumerate(vendor_ids)}
    return sorted(rows, key=lambda r: order.get(r["id"], 999))


# ─────────────────────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    brief: str

class ShortlistRequest(BaseModel):
    brief: dict
    selected_vendor_ids: list[str]

class PreviewRFQsRequest(BaseModel):
    brief: dict
    selected_vendor_ids: list[str]


# ─────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/vendors")
def api_vendors(
    q: str = "",
    category: str = "",
    city: str = "",
    min_rating: float = 0,
    has_email: bool = False,
    limit: int = Query(default=24, le=100),
    offset: int = 0,
):
    """Search and filter the vendor database."""
    query = sb.table("vendors").select("*", count="exact")

    if q:
        query = query.or_(
            f"name.ilike.%{q}%,tags.ilike.%{q}%,description.ilike.%{q}%,amenities.ilike.%{q}%"
        )
    if category:
        query = query.eq("category", category)
    if city:
        query = query.eq("city", city)
    if min_rating > 0:
        query = query.gte("rating_external", min_rating)
    if has_email:
        query = query.neq("email", None).neq("email", "")

    query = query.order("name").range(offset, offset + limit - 1)
    result = query.execute()

    # Distinct cities and categories for filter dropdowns
    cities_res = sb.table("vendors").select("city").execute()
    cats_res = sb.table("vendors").select("category").execute()
    cities = sorted({r["city"] for r in cities_res.data if r.get("city")})
    categories = sorted({r["category"] for r in cats_res.data if r.get("category")})

    return {
        "vendors": result.data,
        "total": result.count or len(result.data),
        "cities": cities,
        "categories": categories,
    }


@app.get("/api/vendors/search")
def api_vendors_quick_search(q: str = "", limit: int = Query(default=8, le=20)):
    """Lightweight search for Cmd+K palette — returns minimal fields."""
    if not q or len(q) < 2:
        return {"results": []}

    result = (
        sb.table("vendors")
        .select("id,name,category,city,email,website,rating_external")
        .or_(f"name.ilike.%{q}%,tags.ilike.%{q}%,description.ilike.%{q}%")
        .order("name")
        .limit(limit)
        .execute()
    )
    return {"results": result.data}


@app.post("/api/route")
def api_route(req: RouteRequest):
    """Parses brief and returns matched vendors per category."""
    logger.info("POST /api/route — brief: %.80s", req.brief)
    try:
        result = route(req.brief)
        return result
    except Exception as exc:
        logger.error("Route failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/preview-rfqs")
def api_preview_rfqs(req: PreviewRFQsRequest):
    """
    Generates branded RFQ email previews for all selected vendors.
    Calls the real rfq_generator (LLM) — no emails are sent.
    Up to 5 vendors are generated concurrently to keep latency low.
    """
    logger.info("POST /api/preview-rfqs — %d vendors", len(req.selected_vendor_ids))
    vendors = fetch_vendors_by_ids(req.selected_vendor_ids)
    if not vendors:
        raise HTTPException(status_code=400, detail="No vendors found")

    brief    = req.brief
    event_id = "demo"

    def make_preview(vendor: dict) -> dict:
        vid       = vendor["id"]
        name      = vendor.get("name", "Vendor")
        cat       = vendor.get("category", "venue")
        has_email = bool(vendor.get("email"))
        try:
            body     = generate_email_body(vendor, brief)
            form_url = build_form_url(event_id, vid, name, cat)
            subject  = (
                f"Quote request — "
                f"{brief.get('event_type', 'corporate event').title()} "
                f"for {brief.get('headcount', '~50')} people, "
                f"{brief.get('city', 'London')}"
            )
            return {
                "vendor_id":    vid,
                "vendor_name":  name,
                "category":     cat,
                "subject":      subject,
                "plain_body":   body,
                "has_email":    has_email,
                "email_to":     vendor.get("email") or "(no email on file)",
                "website":      vendor.get("website"),
                "description":  vendor.get("description"),
            }
        except Exception as exc:
            logger.warning("RFQ preview failed for %s: %s", name, exc)
            return {
                "vendor_id":   vid,
                "vendor_name": name,
                "category":    cat,
                "has_email":   has_email,
                "error":       str(exc),
            }

    results: dict = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(make_preview, v): v["id"] for v in vendors}
        for fut in as_completed(futures):
            results[futures[fut]] = fut.result()

    # Restore original selection order
    previews = [results[v["id"]] for v in vendors if v["id"] in results]
    return {"previews": previews, "total": len(previews)}


@app.post("/api/shortlist")
def api_shortlist(req: ShortlistRequest):
    """
    Builds a shortlist from ALL selected vendor IDs.
    Generates a unique synthetic response per vendor using their actual DB
    data, then runs the full parse → normalise → rank pipeline.
    Previously used one hardcoded response per category; now every vendor
    gets a distinct, realistic quote derived from their record.
    """
    logger.info(
        "POST /api/shortlist — %d vendors selected", len(req.selected_vendor_ids)
    )

    brief    = req.brief
    event_id = "api-demo"
    vendors  = fetch_vendors_by_ids(req.selected_vendor_ids)

    if not vendors:
        raise HTTPException(status_code=400, detail="No vendors found for given IDs")

    parsed_quotes: list[dict] = []

    for vendor in vendors:
        cat   = vendor.get("category", "venue")
        synth = generate_synthetic_response(vendor, brief)
        raw   = synth["response"]

        # Fast direct extraction — synthetic responses have known structure,
        # so we read the fields we built in and skip the LLM extraction call.
        extracted = _extract_synthetic(synth, vendor, brief)
        conf      = extracted.pop("_confidence_score", 0.55)

        parsed_quotes.append({
            "quote_id":         None,
            "extracted":        extracted,
            "confidence_score": conf,
            "warnings":         [],
            "extraction_notes": "synthetic — direct extraction, no LLM",
            "response_type":    synth["type"],
            "vendor_id":        vendor["id"],
            "vendor_name":      vendor.get("name", "Unknown"),
            "category":         cat,
        })

    if not parsed_quotes:
        raise HTTPException(
            status_code=500,
            detail="No quotes could be extracted from synthetic responses"
        )

    # Normalise
    try:
        normalised = normalise_quotes(
            quotes=[
                {
                    "quote_id":         q.get("quote_id"),
                    "vendor_id":        q.get("vendor_id"),
                    "vendor_name":      q.get("vendor_name"),
                    "category":         q.get("category"),
                    "confidence_score": q.get("confidence_score"),
                    **q.get("extracted", {}),
                }
                for q in parsed_quotes
            ],
            brief      = brief,
            save_to_db = False,
        )
    except Exception as exc:
        logger.error("normalise_quotes failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Normalisation failed: {exc}")

    # Rank
    try:
        ranked = rank_quotes(
            normalised_quotes = normalised["normalised_quotes"],
            brief             = brief,
            event_id          = event_id,
            save_to_db        = False,
        )
    except Exception as exc:
        logger.error("rank_quotes failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ranking failed: {exc}")

    # Budget summary using top vendor per category
    top_per_cat: dict = {}
    for q in ranked.get("ranked", []):
        if q["category"] not in top_per_cat:
            top_per_cat[q["category"]] = q

    total_vat = sum(
        q["normalised"].get("total_inc_vat", 0) or 0
        for q in top_per_cat.values()
    )
    budget    = brief.get("budget_total") or 0
    remaining = budget - total_vat

    # Flatten shortlist for frontend
    shortlist_items = []
    for q in ranked.get("ranked", []):
        n = q.get("normalised", {})
        shortlist_items.append({
            "rank":               q.get("rank"),
            "vendor_name":        q.get("vendor_name"),
            "category":           q.get("category"),
            "score":              q.get("rank_score"),
            "total_inc_vat":      n.get("total_inc_vat"),
            "total_per_head":     n.get("total_per_head"),
            "components":         q.get("components", {}),
            "missing_components": q.get("missing_components", []),
            "inclusions":         [
                k.replace("_", " ").title()
                for k, v in q.get("components", {}).items()
                if v == "included"
            ],
            "exclusions":         [
                k.replace("_", " ").title()
                for k, v in q.get("components", {}).items()
                if v == "excluded"
            ],
            "availability":       q.get("availability"),
            "confidence_score":   q.get("confidence_score"),
            "score_breakdown":    q.get("score_breakdown", {}),
        })

    # Flatten by_category for the frontend category-winner cards
    by_category_flat: dict = {}
    for cat, items in ranked.get("by_category", {}).items():
        by_category_flat[cat] = [
            {
                "vendor_name":     q.get("vendor_name"),
                "score":           q.get("rank_score"),
                "total_inc_vat":   q.get("normalised", {}).get("total_inc_vat"),
                "total_per_head":  q.get("normalised", {}).get("total_per_head"),
                "score_breakdown": q.get("score_breakdown", {}),
                "inclusions":      [
                    k.replace("_", " ").title()
                    for k, v in q.get("components", {}).items()
                    if v == "included"
                ],
            }
            for q in items[:3]
        ]

    categories = list(by_category_flat.keys())

    return {
        "shortlist":      shortlist_items,
        "by_category":    by_category_flat,
        "recommendation": ranked.get("recommendation", ""),
        "budget_summary": {
            "total_inc_vat": round(total_vat, 2),
            "budget":        budget,
            "remaining":     round(remaining, 2),
            "within_budget": remaining >= 0,
        },
        "meta": {
            "vendors_evaluated": len(req.selected_vendor_ids),
            "vendors_quoted":    len(parsed_quotes),
            "categories":        categories,
        },
    }
