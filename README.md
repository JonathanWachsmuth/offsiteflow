# OffsiteFlow

AI-powered corporate event planning platform. Automates vendor discovery, RFQ outreach, response extraction, and shortlist generation.

---

## Setup

**1. Clone and create a virtual environment**

```bash
git clone https://github.com/JonathanWachsmuthIC/OffsiteFlow.git
cd OffsiteFlow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment variables**

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
TALLY_FORM_URL=https://tally.so/r/YOUR_FORM_ID

SMTP_EMAIL=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Gmail App Password — not your account password
```

> **Gmail SMTP:** Your account password will not work. Generate an App Password at  
> Google Account → Security → App Passwords (requires 2-Step Verification enabled).

**3. Initialise the database**

```bash
python3 -m db.migrate
```

This creates `data/vendors.db` and applies all migrations in `db/migrations/`.

---

## Running the pipeline

**Interactive mode (default — prompts for vendor approval before sending)**

```bash
python3 -m pipeline.cli
```

**Common flags**

```bash
# Send real emails instead of dry run
python3 -m pipeline.cli --send

# Redirect all outbound emails to your own address for testing
python3 -m pipeline.cli --send --override-to you@example.com

# Skip the vendor approval prompt (auto-approves top 3 per category)
python3 -m pipeline.cli --no-interactive

# Use real vendor responses from DB instead of synthetic ones
python3 -m pipeline.cli --real-responses

# Pass a custom event brief
python3 -m pipeline.cli --brief "Team dinner for 20 people in Manchester, budget £3,000"

# Save the shortlist to the database
python3 -m pipeline.cli --save

# Verbose logging
python3 -m pipeline.cli --log-level INFO
```

---

## Running the app

```bash
streamlit run app.py
```

Opens the Streamlit UI at `http://localhost:8501`.

---

## Populating the vendor database

**Option A — Google Places API (automated)**

```bash
python3 -m pipeline.collect.api_fetch
```

Collects vendors across venue / catering / activity / transport categories for London. Validates assumption A1.

**Option B — Manual CSV import**

Place your CSV at `data/raw/manual/vendors_seed.csv` with columns:  
`name, category, city, email, website` (+ optional enrichment columns).

```bash
python3 -m pipeline.collect.manual_import
```

**Option C — Contact extraction**

Extract emails from vendor websites already in the database:

```bash
python3 -m pipeline.collect.contact_extractor
```

---

## Running experiments

Each experiment file is self-contained and logs results to the `experiments` table.

```bash
# A1 — Vendor availability via Google Places API
python3 -m experiments.A1_vendor_availability

# A2 — Contact reachability (email extraction)
python3 -m experiments.A2_contact_reachability

# A4 — LLM brief parsing
python3 -m experiments.A4_llm_brief_parsing

# A5 — Quote extraction accuracy
python3 -m experiments.A5_response_extraction

# A7 — Offer normalisation
python3 -m experiments.A7_offer_normalisation

# A8 — Offer filtering and ranking
python3 -m experiments.A8_offer_filtering
```

---

## Running tests

```bash
pytest tests/
```

Individual test files:

```bash
pytest tests/test_router.py     # LLM brief parsing and vendor routing
pytest tests/test_parser.py     # Quote extraction from vendor responses
pytest tests/test_normaliser.py # Price normalisation and component detection
pytest tests/test_ranker.py     # Vendor ranking and scoring
```

Tests mock all external calls (LLM API, SMTP, SQLite) so no credentials are needed.

---

## Project structure

```
offsiteflow/
├── app.py                      # Streamlit UI
├── config/
│   └── settings.py             # All config loaded from .env
├── db/
│   ├── connection.py           # SQLite context manager (get_db)
│   ├── migrate.py              # Migration runner
│   └── migrations/
│       └── 001_initial.sql     # Full schema
├── pipeline/
│   ├── cli.py                  # CLI entry point (argparse + test data)
│   ├── run.py                  # Pure orchestrator (no test data)
│   ├── collect/
│   │   ├── api_fetch.py        # Google Places vendor collection
│   │   ├── contact_extractor.py # Email extraction from websites
│   │   └── manual_import.py    # CSV → database import
│   ├── match/
│   │   └── llm_router.py       # Brief parsing + vendor matching
│   ├── outreach/
│   │   ├── rfq_generator.py    # Branded RFQ email generation
│   │   └── email_sender.py     # SMTP send + outreach logging
│   ├── extract/
│   │   └── quote_parser.py     # LLM extraction from vendor replies
│   └── normalise/
│       ├── normaliser.py       # Price normalisation
│       └── ranker.py           # Vendor scoring and shortlist
├── tests/
│   ├── fixtures/
│   │   ├── test_briefs.py      # Test event briefs
│   │   ├── synthetic_responses.py # Simulated vendor replies
│   │   └── test_vendors.py     # Test vendor records
│   ├── test_router.py
│   ├── test_parser.py
│   ├── test_normaliser.py
│   └── test_ranker.py
├── experiments/
│   ├── A1_vendor_availability.py
│   ├── A2_contact_reachability.py
│   ├── A3_vendor_response_rate.py
│   ├── A4_llm_brief_parsing.py
│   ├── A5_response_extraction.py
│   ├── A7_offer_normalisation.py
│   └── A8_offer_filtering.py
├── data/
│   ├── vendors.db
│   └── raw/
│       ├── manual/             # Vendor CSVs
│       ├── quotes/             # Raw vendor reply files
│       └── scraped/            # Google Places JSON output
└── output/
    └── shortlists/             # Generated shortlist JSON files
```

---

## Validation board

| ID  | Assumption                              | Status      | Evidence                        |
|-----|-----------------------------------------|-------------|---------------------------------|
| A1  | ≥200 vendors accessible via Places API  | VALIDATED   | 240 vendors found in London     |
| A2  | ≥60% of vendors have extractable email  | VALIDATED   | 29/40 = 72.5% in manual test    |
| A3  | ≥50% respond to RFQ within 72 hours     | NOT TESTED  | —                               |
| A4  | LLM can parse brief + route vendors     | NOT TESTED  | —                               |
| A5  | LLM extracts pricing with ≥80% accuracy | NOT TESTED  | —                               |
| A7  | Offers normalised into comparable format| NOT TESTED  | —                               |
| A8  | System ranks + filters offers auto      | NOT TESTED  | —                               |
| A9  | Shortlist clear enough to book from     | NOT TESTED  | —                               |
| A10 | Output format fits planner workflow     | NOT TESTED  | —                               |
| A11 | ≥3 viable vendors surfaced per brief    | NOT TESTED  | —                               |
| A12 | Full pipeline completes within 48 hours | NOT TESTED  | —                               |
