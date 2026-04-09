# pipeline/run.py
# ─────────────────────────────────────────────────────────────
# End-to-end pipeline orchestrator.
# Pure orchestration — no CLI args, no test data.
# Call run() from CLI (pipeline/cli.py) or the Streamlit app.
#
# Flow:
#   Stage 1 — Parse brief + route to vendors
#   Stage 2 — RFQ generation and outreach
#   Stage 3 — Response collection + extraction
#   Stage 4 — Normalisation
#   Stage 5 — Ranking + shortlist
# ─────────────────────────────────────────────────────────────

import json
import uuid
import logging
import os
from datetime import datetime, timezone

from pipeline.match.llm_router       import route
from pipeline.outreach.rfq_generator import generate_rfq
from pipeline.outreach.email_sender  import send_single
from pipeline.extract.quote_parser   import parse_quote
from pipeline.normalise.normaliser   import normalise_quotes
from pipeline.normalise.ranker       import rank_quotes
from config.settings                 import SHORTLIST_OUTPUT_DIR
from db.connection                   import get_db

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────────────────────

def get_or_create_default_org(conn) -> str:
    """Gets or creates a default organisation for pipeline runs."""
    row = conn.execute("SELECT id FROM organisations LIMIT 1").fetchone()
    if row:
        return row["id"]

    org_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO organisations (id, name) VALUES (?, ?)",
        (org_id, "OffsiteFlow Default")
    )
    return org_id


def save_event(conn, brief: dict) -> str:
    """Saves event brief to events table. Returns event_id."""
    event_id = str(uuid.uuid4())
    org_id   = get_or_create_default_org(conn)

    conn.execute("""
        INSERT INTO events (
            id, org_id, name, type, city, country,
            date_start, headcount, budget_total,
            budget_currency, brief_text, requirements, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, org_id,
        f"{brief.get('event_type', 'offsite').title()} — {brief.get('city', 'London')}",
        brief.get("event_type", "offsite"),
        brief.get("city", "London"),
        "GB",
        brief.get("date_start"),
        brief.get("headcount"),
        brief.get("budget_total"),
        "GBP",
        brief.get("brief_text", ""),
        brief.get("requirements", ""),
        "sourcing"
    ))
    return event_id


# ─────────────────────────────────────────────────────────────
# STAGE 1 — BRIEF PARSING AND ROUTING
# ─────────────────────────────────────────────────────────────

def stage_1_parse_and_route(brief_input) -> dict:
    logger.info("Stage 1 — Brief parsing and vendor routing")
    print(f"\n{'─'*55}")
    print(f"  STAGE 1 — Brief parsing and vendor routing")
    print(f"{'─'*55}")
    return route(brief_input)


# ─────────────────────────────────────────────────────────────
# CANDIDATE REVIEW (interactive)
# ─────────────────────────────────────────────────────────────

def present_candidates(routing_result: dict, brief: dict) -> list:
    """
    Presents matched vendors for user review before any outreach.
    Returns list of approved candidate dicts.
    In non-interactive mode (EOFError), approves all vendors with email.
    """
    matches = routing_result["matches"]

    print(f"\n{'='*55}")
    print(f"  CANDIDATE VENDORS — REVIEW BEFORE OUTREACH")
    print(f"  {brief.get('event_type','offsite').title()} · "
          f"{brief.get('headcount')} people · "
          f"{brief.get('city')} · £{brief.get('budget_total')}")
    print(f"{'='*55}")

    all_candidates = []
    idx = 1

    for category, vendors in matches.items():
        print(f"\n  {category.upper()}")
        print(f"  {'─'*50}")
        for v in vendors:
            has_email  = bool(v.get("email"))
            email_str  = v["email"] if has_email else "no email"
            price_str  = f" · from £{v['price_from']}" if v.get("price_from") else ""
            rating_str = f" · ★{v['rating_external']}" if v.get("rating_external") else ""
            icon       = "✉" if has_email else "✗"

            print(f"\n  [{idx}] {v['name']}")
            print(f"       {icon}  {email_str}{price_str}{rating_str}")
            if v.get("reason"):
                print(f"       {v['reason'][:72]}")

            all_candidates.append({"idx": idx, "vendor": v, "category": category})
            idx += 1

    with_email = sum(1 for c in all_candidates if c["vendor"].get("email"))
    print(f"\n{'─'*55}")
    print(f"  {len(all_candidates)} candidates · {with_email} have email")
    print(f"{'─'*55}")
    print(f"\n  Enter → approve all with email | 1,3,5 → specific | none → exit\n")

    try:
        selection = input("  Your selection: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        selection = ""
        print("  (Non-interactive — approving all with email)")

    if selection == "none":
        print("\n  No vendors selected. Exiting.")
        return []

    if selection in ("", "all"):
        approved = [c for c in all_candidates if c["vendor"].get("email")]
    else:
        try:
            ids      = [int(x.strip()) for x in selection.split(",")]
            approved = [c for c in all_candidates
                        if c["idx"] in ids and c["vendor"].get("email")]
        except ValueError:
            print("  Invalid selection — no vendors approved.")
            return []

    if not approved:
        return []

    print(f"\n  Selected ({len(approved)}):")
    for c in approved:
        print(f"    [{c['idx']}] {c['vendor']['name']:<35} {c['category']}")

    print(f"\n  Confirm outreach? (yes / no)")
    try:
        confirm = input("  Confirm: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        confirm = "no"
        print("  (Non-interactive — defaulting to no)")

    if confirm not in ("yes", "y"):
        print("  Outreach cancelled.")
        return []

    return approved


# ─────────────────────────────────────────────────────────────
# STAGE 2 — OUTREACH
# ─────────────────────────────────────────────────────────────

def stage_2_outreach(approved: list, brief: dict, event_id: str,
                     dry_run: bool = True, override_to: str = None) -> list:
    """
    Generates and optionally sends RFQ emails for approved vendors.
    dry_run=True: generates + logs but does not send.
    """
    logger.info("Stage 2 — RFQ generation (%s)", "dry run" if dry_run else "live")
    print(f"\n{'─'*55}")
    print(f"  STAGE 2 — RFQ generation")
    print(f"  {'DRY RUN — not sent' if dry_run else 'LIVE — sending'}")
    print(f"{'─'*55}")

    sent_rfqs = []

    for candidate in approved:
        vendor   = candidate["vendor"]
        category = candidate["category"]

        if not vendor.get("email"):
            continue

        rfq = generate_rfq(vendor, brief, event_id)
        if not rfq:
            logger.warning("RFQ generation failed for %s", vendor["name"])
            continue

        if dry_run:
            print(f"\n  [DRY RUN] To:      {vendor['email']}")
            print(f"            Subject: {rfq['subject']}")
            sent_rfqs.append({
                "vendor_id":   vendor["id"],
                "vendor_name": vendor["name"],
                "category":    category,
                "outreach_id": None,
                "status":      "dry_run",
                "vendor":      vendor,
            })
        else:
            result = send_single(rfq, event_id=event_id,
                                 override_to=override_to, dry_run=False)
            sent_rfqs.append({
                "vendor_id":   vendor["id"],
                "vendor_name": vendor["name"],
                "category":    category,
                "outreach_id": result.get("outreach_id"),
                "status":      result.get("status"),
                "vendor":      vendor,
            })

    mode = "generated (not sent)" if dry_run else "sent"
    logger.info("Stage 2 complete — %d RFQs %s", len(sent_rfqs), mode)
    print(f"\n  RFQs {mode}: {len(sent_rfqs)}")
    return sent_rfqs


# ─────────────────────────────────────────────────────────────
# STAGE 3 — RESPONSE COLLECTION
# ─────────────────────────────────────────────────────────────

def stage_3_collect_responses(sent_rfqs: list, brief: dict, event_id: str,
                               synthetic: bool = True,
                               synthetic_responses: dict = None) -> list:
    """
    Collects and parses vendor responses.
    synthetic=True: uses provided synthetic_responses dict.
    synthetic=False: checks outreach table for real replies.
    """
    logger.info("Stage 3 — Response collection (%s)", "synthetic" if synthetic else "live")
    print(f"\n{'─'*55}")
    print(f"  STAGE 3 — Response collection")
    print(f"  {'SYNTHETIC' if synthetic else 'LIVE from DB'}")
    print(f"{'─'*55}")

    parsed_quotes = []

    for rfq_record in sent_rfqs:
        vendor   = rfq_record["vendor"]
        category = rfq_record["category"]

        if synthetic:
            if not synthetic_responses:
                logger.warning("synthetic=True but no synthetic_responses provided")
                continue
            synth = synthetic_responses.get(category)
            if not synth:
                continue
            raw_response = synth["data"] if synth["type"] == "form" else synth["text"]
            print(f"\n  Synthetic {synth['type']}: {vendor['name']}")

        else:
            with get_db() as conn:
                row = conn.execute("""
                    SELECT raw_response FROM outreach
                    WHERE id = ? AND raw_response IS NOT NULL
                """, (rfq_record.get("outreach_id"),)).fetchone()

            if not row or not row["raw_response"]:
                print(f"  No response yet: {vendor['name']}")
                continue

            raw_response = row["raw_response"]
            print(f"\n  Real response: {vendor['name']}")

        result = parse_quote(
            raw_response = raw_response,
            vendor       = vendor,
            brief        = brief,
            outreach_id  = rfq_record.get("outreach_id", ""),
            event_id     = event_id,
            save_to_db   = not synthetic
        )
        parsed_quotes.append({
            **result,
            "vendor_id":   vendor["id"],
            "vendor_name": vendor["name"],
            "category":    category,
        })

    logger.info("Stage 3 complete — %d responses", len(parsed_quotes))
    print(f"\n  Parsed: {len(parsed_quotes)} responses")
    return parsed_quotes


# ─────────────────────────────────────────────────────────────
# STAGE 4 — NORMALISATION
# ─────────────────────────────────────────────────────────────

def stage_4_normalise(parsed_quotes: list, brief: dict) -> dict:
    logger.info("Stage 4 — Normalisation")
    print(f"\n{'─'*55}")
    print(f"  STAGE 4 — Normalisation")
    print(f"{'─'*55}")

    return normalise_quotes(
        quotes=[
            {
                "quote_id":         q.get("quote_id"),
                "vendor_id":        q.get("vendor_id"),
                "vendor_name":      q.get("vendor_name"),
                "category":         q.get("category"),
                "confidence_score": q.get("confidence_score"),
                **q.get("extracted", {})
            }
            for q in parsed_quotes
        ],
        brief      = brief,
        save_to_db = False
    )


# ─────────────────────────────────────────────────────────────
# STAGE 5 — RANKING
# ─────────────────────────────────────────────────────────────

def stage_5_rank(normalised: dict, brief: dict,
                 event_id: str, save_to_db: bool = False) -> dict:
    logger.info("Stage 5 — Ranking")
    print(f"\n{'─'*55}")
    print(f"  STAGE 5 — Ranking and shortlist")
    print(f"{'─'*55}")

    return rank_quotes(
        normalised_quotes = normalised["normalised_quotes"],
        brief             = brief,
        event_id          = event_id,
        save_to_db        = save_to_db
    )


# ─────────────────────────────────────────────────────────────
# OUTPUT FORMATTER
# ─────────────────────────────────────────────────────────────

def print_shortlist(result: dict, brief: dict):
    """Prints formatted shortlist and saves JSON to output/shortlists/."""
    print(f"\n{'='*55}")
    print(f"  OFFSITEFLOW — EVENT SHORTLIST")
    print(f"{'='*55}")
    print(f"  {brief.get('event_type','offsite').title()} · "
          f"{brief.get('city')} · "
          f"{brief.get('headcount')} people · £{brief.get('budget_total')}")
    print(f"{'─'*55}")
    print(f"\n  RECOMMENDATION\n  {result['recommendation']}")
    print(f"\n{'─'*55}\n  SHORTLIST BY CATEGORY")

    for category, quotes in result["by_category"].items():
        print(f"\n  {category.upper()}")
        for q in quotes:
            n = q["normalised"]
            print(f"\n    #{q['rank']} {q['vendor_name']}")
            print(f"         Total inc VAT:  £{n.get('total_inc_vat', 'N/A')}")
            print(f"         Per head:       £{n.get('total_per_head', 'N/A')}")
            print(f"         Score:          {q['rank_score']:.3f}")
            included = [c for c, s in q["components"].items() if s == "included"]
            print(f"         Includes:       {', '.join(included)}")
            if q["missing_components"]:
                print(f"         Missing:        {', '.join(q['missing_components'])}")

    ranked      = result["ranked"]
    top_per_cat = {}
    for q in ranked:
        if q["category"] not in top_per_cat:
            top_per_cat[q["category"]] = q

    if top_per_cat:
        total_combo = sum(
            q["normalised"].get("total_inc_vat", 0)
            for q in top_per_cat.values()
            if q["normalised"].get("total_inc_vat")
        )
        budget    = brief.get("budget_total", 0)
        remaining = budget - total_combo
        status    = "within budget" if remaining >= 0 else "OVER BUDGET"

        print(f"\n{'─'*55}\n  BUDGET SUMMARY\n{'─'*55}")
        for cat, q in top_per_cat.items():
            t = q["normalised"].get("total_inc_vat", 0)
            print(f"  {cat.title():<14} {q['vendor_name']:<28} £{t:>7,.0f}")
        print(f"  {'─'*48}")
        print(f"  {'Total':<43} £{total_combo:>7,.0f}")
        print(f"  {'Budget':<43} £{budget:>7,.0f}")
        print(f"  {'Remaining':<43} £{abs(remaining):>7,.0f}  ({status})")

    print(f"\n{'='*55}\n")

    os.makedirs(SHORTLIST_OUTPUT_DIR, exist_ok=True)
    path = os.path.join(
        SHORTLIST_OUTPUT_DIR,
        f"shortlist_{brief.get('city','london').lower()}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(path, "w") as f:
        json.dump({"brief": brief, "shortlist": result,
                   "generated": datetime.now(timezone.utc).isoformat()},
                  f, indent=2, default=str)
    print(f"  Saved to {path}")


# ─────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────

def run(brief_input,
        dry_run:             bool = True,
        synthetic:           bool = True,
        synthetic_responses: dict = None,
        override_to:         str  = None,
        save_to_db:          bool = False,
        interactive:         bool = True) -> dict:
    """
    Runs the full OffsiteFlow pipeline end-to-end.

    Args:
        brief_input:          free-text string or structured brief dict
        dry_run:              if True, generate RFQs but do not send emails
        synthetic:            if True, use synthetic_responses for stage 3
        synthetic_responses:  dict keyed by category with vendor reply data
        override_to:          redirect all emails to this address
        save_to_db:           write shortlist to database
        interactive:          if False, skip candidate approval prompt
    """
    logger.info("Pipeline starting — dry_run=%s synthetic=%s", dry_run, synthetic)
    print(f"\n{'='*55}")
    print(f"  OFFSITEFLOW PIPELINE")
    print(f"  Emails:    {'DISABLED (dry run)' if dry_run else 'ENABLED'}")
    print(f"  Responses: {'SYNTHETIC' if synthetic else 'LIVE from DB'}")
    print(f"{'='*55}")

    routing_result      = stage_1_parse_and_route(brief_input)
    brief               = routing_result["brief"]
    brief["brief_text"] = str(brief_input)

    with get_db() as conn:
        event_id = save_event(conn, brief)

    logger.info("Event saved: %s — %d vendors matched",
                event_id, routing_result["total_matched"])
    print(f"\n  Event ID: {event_id}")
    print(f"  Vendors matched: {routing_result['total_matched']}")

    if interactive:
        approved = present_candidates(routing_result, brief)
        if not approved:
            return {"event_id": event_id, "status": "cancelled"}
    else:
        approved = [
            {"vendor": v, "category": cat, "idx": i}
            for i, (cat, vendors) in enumerate(routing_result["matches"].items())
            for v in vendors[:3]
            if v.get("email")
        ]
        print(f"\n  Auto-approved {len(approved)} vendors")

    sent_rfqs = stage_2_outreach(approved, brief, event_id,
                                 dry_run=dry_run, override_to=override_to)
    if not sent_rfqs:
        return {"event_id": event_id, "sent": 0}

    parsed_quotes = stage_3_collect_responses(
        sent_rfqs, brief, event_id,
        synthetic=synthetic, synthetic_responses=synthetic_responses
    )
    if not parsed_quotes:
        print("\n  No responses collected. Re-run after vendors reply.")
        return {"event_id": event_id, "sent": len(sent_rfqs)}

    normalised = stage_4_normalise(parsed_quotes, brief)
    ranked     = stage_5_rank(normalised, brief, event_id, save_to_db=save_to_db)
    print_shortlist(ranked, brief)

    logger.info("Pipeline complete — event_id=%s", event_id)
    return {
        "event_id":  event_id,
        "brief":     brief,
        "sent":      len(sent_rfqs),
        "responses": len(parsed_quotes),
        "shortlist": ranked,
    }
