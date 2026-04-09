# api.py
# ─────────────────────────────────────────────────────────────
# OffsiteFlow — FastAPI backend
# Run: uvicorn api:app --reload --port 8000
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.match.llm_router     import route
from pipeline.extract.quote_parser import parse_quote
from pipeline.normalise.normaliser import normalise_quotes
from pipeline.normalise.ranker     import rank_quotes
from config.settings               import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OffsiteFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# SYNTHETIC RESPONSES (one per category)
# ─────────────────────────────────────────────────────────────

SYNTHETIC = {
    "venue": {
        "type": "email",
        "response": (
            "Thank you for your enquiry. For 45 people, full day hire is £4,500 + VAT (20%). "
            "Includes AV equipment, WiFi, coordinator, outdoor terrace. "
            "Excludes catering. Available June. Max capacity 60."
        ),
    },
    "catering": {
        "type": "form",
        "response": {
            "available":        "Yes",
            "maximum_capacity": 80,
            "price_per_head":   85,
            "inclusions":       "food, staff, crockery, linen",
            "exclusions":       "venue, drinks",
            "notes":            "12.5% service charge. VAT 20%.",
        },
    },
    "activity": {
        "type": "email",
        "response": (
            "Outdoor challenge programme: £65 per person half-day. "
            "Includes equipment, facilitators, debrief. "
            "Excludes venue, catering. Available June 15+. Groups 20-80."
        ),
    },
    "transport": {
        "type": "email",
        "response": (
            "We can provide coach transfers for 45 people. "
            "£8 per person per trip. Includes driver and fuel. "
            "Available on request. Min 2 hours notice."
        ),
    },
}


# ─────────────────────────────────────────────────────────────
# DB HELPER
# ─────────────────────────────────────────────────────────────

def fetch_vendors_by_ids(vendor_ids: list[str]) -> list[dict]:
    """Fetches full vendor records from vendors.db by ID list."""
    if not vendor_ids:
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" for _ in vendor_ids)
    rows = conn.execute(
        f"SELECT * FROM vendors WHERE id IN ({placeholders})", vendor_ids
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    brief: str


class ShortlistRequest(BaseModel):
    brief: dict
    selected_vendor_ids: list[str]


# ─────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


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


@app.post("/api/shortlist")
def api_shortlist(req: ShortlistRequest):
    """
    Builds a shortlist from selected vendor IDs using synthetic responses.
    One synthetic response per category; uses the first selected vendor
    from each category.
    """
    logger.info(
        "POST /api/shortlist — %d vendors selected", len(req.selected_vendor_ids)
    )

    brief      = req.brief
    event_id   = "api-demo"
    vendors    = fetch_vendors_by_ids(req.selected_vendor_ids)

    if not vendors:
        raise HTTPException(status_code=400, detail="No vendors found for given IDs")

    # Group selected vendors by category — one per category
    seen_categories: set[str] = set()
    candidates: list[dict]    = []
    for v in vendors:
        cat = v.get("category", "venue")
        if cat not in seen_categories:
            seen_categories.add(cat)
            candidates.append(v)

    parsed_quotes: list[dict] = []

    for vendor in candidates:
        cat    = vendor.get("category", "venue")
        synth  = SYNTHETIC.get(cat, SYNTHETIC["venue"])
        raw    = synth["response"]

        try:
            result = parse_quote(
                raw_response = raw,
                vendor       = vendor,
                brief        = brief,
                outreach_id  = f"api-{vendor['id']}",
                event_id     = event_id,
                save_to_db   = False,
            )
            parsed_quotes.append({
                **result,
                "vendor_id":   vendor["id"],
                "vendor_name": vendor.get("name", "Unknown"),
                "category":    cat,
            })
        except Exception as exc:
            logger.warning("parse_quote failed for %s: %s", vendor.get("name"), exc)
            continue

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

    # Build budget summary
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

    # Flatten shortlist for easier frontend consumption
    shortlist_items = []
    for q in ranked.get("ranked", []):
        n = q.get("normalised", {})
        shortlist_items.append({
            "rank":              q.get("rank"),
            "vendor_name":       q.get("vendor_name"),
            "category":          q.get("category"),
            "score":             q.get("rank_score"),
            "total_inc_vat":     n.get("total_inc_vat"),
            "total_per_head":    n.get("total_per_head"),
            "components":        q.get("components", {}),
            "missing_components": q.get("missing_components", []),
            "inclusions":        [
                k.replace("_", " ").title()
                for k, v in q.get("components", {}).items()
                if v == "included"
            ],
            "exclusions":        [
                k.replace("_", " ").title()
                for k, v in q.get("components", {}).items()
                if v == "excluded"
            ],
            "availability":      q.get("availability"),
            "confidence_score":  q.get("confidence_score"),
            "score_breakdown":   q.get("score_breakdown", {}),
        })

    return {
        "shortlist":    shortlist_items,
        "by_category":  ranked.get("by_category", {}),
        "recommendation": ranked.get("recommendation", ""),
        "budget_summary": {
            "total_inc_vat":  round(total_vat, 2),
            "budget":         budget,
            "remaining":      round(remaining, 2),
            "within_budget":  remaining >= 0,
        },
    }
