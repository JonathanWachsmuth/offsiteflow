-- ==============================================
-- OFFSITEFLOW DATABASE SCHEMA
-- Version 1.0 | SQLite
-- ==============================================

PRAGMA foreign_keys = ON;

-- ==============================================
-- ORGANISATIONS
-- The company using OffsiteFlow
-- ==============================================

CREATE TABLE organisations (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    size_min            INTEGER,
    size_max            INTEGER,
    industry            TEXT,
    budget_rules        TEXT,        -- JSON: {"max_per_head": 150, "approval_threshold": 5000}
    cost_centers        TEXT,        -- JSON: ["Marketing", "HR", "Sales"]
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- USERS
-- People within the organisation using the app
-- ==============================================

CREATE TABLE users (
    id                  TEXT PRIMARY KEY,
    org_id              TEXT NOT NULL REFERENCES organisations(id),
    email               TEXT NOT NULL UNIQUE,
    name                TEXT,
    role                TEXT DEFAULT 'planner',  -- planner / admin / viewer
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- EVENTS
-- A single offsite or corporate event
-- ==============================================

CREATE TABLE events (
    id                  TEXT PRIMARY KEY,
    org_id              TEXT NOT NULL REFERENCES organisations(id),
    created_by          TEXT REFERENCES users(id),
    name                TEXT,
    type                TEXT,        -- offsite / team_dinner / workshop / conference
    city                TEXT NOT NULL,
    country             TEXT DEFAULT 'GB',
    date_start          DATE,
    date_end            DATE,
    headcount           INTEGER NOT NULL,
    budget_total        REAL NOT NULL,
    budget_currency     TEXT DEFAULT 'GBP',
    brief_text          TEXT,        -- free text brief fed to LLM router
    requirements        TEXT,        -- JSON: {"outdoor": true, "catering": true, "av": false}
    status              TEXT DEFAULT 'draft',
                                     -- draft / sourcing / shortlisted / booked / completed
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Reusable event templates (for repeat events)
CREATE TABLE event_templates (
    id                  TEXT PRIMARY KEY,
    org_id              TEXT REFERENCES organisations(id),
    based_on_event      TEXT REFERENCES events(id),
    name                TEXT,
    default_type        TEXT,
    default_city        TEXT,
    default_budget      REAL,
    default_headcount   INTEGER,
    requirements        TEXT,        -- JSON
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- VENDORS
-- Supplier entities in the database
-- ==============================================

CREATE TABLE vendors (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    category            TEXT NOT NULL,
                        -- venue / catering / activity / transport / accommodation
    subcategory         TEXT,        -- e.g. "outdoor_venue", "fine_dining", "team_building"
    city                TEXT NOT NULL,
    country             TEXT DEFAULT 'GB',
    address             TEXT,
    capacity_min        INTEGER,
    capacity_max        INTEGER,
    price_from          REAL,
    price_unit          TEXT,        -- per_head / flat / per_day
    currency            TEXT DEFAULT 'GBP',

    -- Contact
    email               TEXT,
    phone               TEXT,
    website             TEXT,
    contact_form        TEXT,

    -- Matching
    description         TEXT,        -- free text fed to LLM router
    amenities           TEXT,        -- JSON: ["wifi", "parking", "outdoor", "av"]
    tags                TEXT,        -- JSON: ["countryside", "modern", "city-centre"]
    sustainability      TEXT,

    -- Logistics
    lead_time_days      INTEGER,     -- how far in advance booking needed
    cancellation_policy TEXT,
    deposit_required    REAL,

    -- Quality signals
    rating_external     REAL,        -- Google/TripAdvisor score
    rating_count        INTEGER,

    -- Source tracking (critical for A2 experiment)
    source              TEXT,        -- manual / google_places / scraped / api
    source_url          TEXT,
    verified            INTEGER DEFAULT 0,
    last_verified       DATE,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Individual contacts within a vendor (separate from vendor identity)
CREATE TABLE vendor_contacts (
    id                  TEXT PRIMARY KEY,
    vendor_id           TEXT NOT NULL REFERENCES vendors(id),
    contact_name        TEXT,
    contact_email       TEXT,
    contact_role        TEXT,
    is_primary          INTEGER DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Org-level preferred vendors (join table, not a column)
CREATE TABLE organisation_vendors (
    org_id              TEXT REFERENCES organisations(id),
    vendor_id           TEXT REFERENCES vendors(id),
    preferred           INTEGER DEFAULT 0,
    notes               TEXT,
    PRIMARY KEY (org_id, vendor_id)
);

-- Vendor performance over time (builds the moat)
CREATE TABLE vendor_reviews (
    id                  TEXT PRIMARY KEY,
    vendor_id           TEXT REFERENCES vendors(id),
    event_id            TEXT REFERENCES events(id),
    rating              INTEGER,     -- 1–5
    response_speed_hrs  INTEGER,     -- hours to first response
    quote_accuracy      INTEGER,     -- did quote match final invoice: 0/1
    would_rebook        INTEGER,     -- 0/1
    notes               TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- PIPELINE: OUTREACH
-- Every RFQ sent to a vendor
-- ==============================================

CREATE TABLE outreach (
    id                  TEXT PRIMARY KEY,
    event_id            TEXT NOT NULL REFERENCES events(id),
    vendor_id           TEXT NOT NULL REFERENCES vendors(id),
    email_to            TEXT NOT NULL,
    email_subject       TEXT,
    email_body          TEXT,        -- the generated RFQ text
    sent_at             DATETIME,
    status              TEXT DEFAULT 'pending',
                        -- pending / sent / bounced / replied / no_response
    raw_response        TEXT,        -- raw email reply text
    response_at         DATETIME,
    raw_file_path       TEXT         -- pointer to stored .eml / .txt
);

-- Full message thread per outreach (multi-turn vendor comms)
CREATE TABLE messages (
    id                  TEXT PRIMARY KEY,
    outreach_id         TEXT NOT NULL REFERENCES outreach(id),
    direction           TEXT NOT NULL,   -- inbound / outbound
    subject             TEXT,
    body                TEXT,
    sent_at             DATETIME,
    raw_file_path       TEXT
);

-- ==============================================
-- PIPELINE: QUOTES
-- Structured data extracted from vendor responses
-- ==============================================

CREATE TABLE quotes (
    id                  TEXT PRIMARY KEY,
    outreach_id         TEXT REFERENCES outreach(id),
    event_id            TEXT NOT NULL REFERENCES events(id),
    vendor_id           TEXT NOT NULL REFERENCES vendors(id),

    -- Versioning (vendors often revise)
    version             INTEGER DEFAULT 1,
    parent_quote_id     TEXT REFERENCES quotes(id),
    superseded          INTEGER DEFAULT 0,

    -- Normalised pricing
    base_price          REAL,
    price_per_head      REAL,
    service_fee         REAL,
    vat_rate            REAL,
    total_estimated     REAL,
    currency            TEXT DEFAULT 'GBP',
    price_unit          TEXT,        -- flat / per_head / per_day

    -- Inclusions
    inclusions          TEXT,        -- JSON: ["AV", "catering", "parking"]
    exclusions          TEXT,        -- JSON: ["accommodation", "transport"]
    capacity_offered    INTEGER,
    availability        INTEGER,     -- 0/1 confirmed for event dates

    -- Extraction quality (key metric for A5/A6 experiments)
    confidence_score    REAL,        -- 0.0–1.0
    extraction_notes    TEXT,        -- LLM notes on uncertainty or gaps
    extracted_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    manually_reviewed   INTEGER DEFAULT 0,

    -- Normalisation state
    normalised          INTEGER DEFAULT 0,
    normalisation_notes TEXT,

    status              TEXT DEFAULT 'extracted'
                        -- extracted / normalised / shortlisted / rejected / booked
);

-- ==============================================
-- OUTPUT: SHORTLISTS
-- The ranked results presented to the planner
-- ==============================================

CREATE TABLE shortlists (
    id                  TEXT PRIMARY KEY,
    event_id            TEXT NOT NULL REFERENCES events(id),
    generated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    status              TEXT DEFAULT 'active'  -- active / archived
);

CREATE TABLE shortlist_items (
    id                  TEXT PRIMARY KEY,
    shortlist_id        TEXT NOT NULL REFERENCES shortlists(id),
    quote_id            TEXT NOT NULL REFERENCES quotes(id),
    rank                INTEGER,
    rank_score          REAL,
    rank_reason         TEXT,        -- LLM explanation (addresses A14 transparency)
    selected            INTEGER DEFAULT 0
);

-- ==============================================
-- BUDGET TRACKING
-- Lightweight ledger for budget evolution
-- ==============================================

CREATE TABLE budget_entries (
    id                  TEXT PRIMARY KEY,
    event_id            TEXT NOT NULL REFERENCES events(id),
    vendor_id           TEXT REFERENCES vendors(id),
    type                TEXT,        -- quote / deposit / payment / adjustment
    amount              REAL,
    currency            TEXT DEFAULT 'GBP',
    notes               TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- EXPERIMENT TRACKING
-- Maps directly to validation board assumptions
-- ==============================================

CREATE TABLE experiments (
    id                  TEXT PRIMARY KEY,
    assumption_id       TEXT NOT NULL,   -- "A1", "A2", "A3" etc.
    hypothesis          TEXT,
    method              TEXT,
    min_success         TEXT,
    result              TEXT,            -- JSON: raw results
    outcome             TEXT,            -- validated / invalidated / inconclusive
    notes               TEXT,
    run_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- INDEXES
-- ==============================================

CREATE INDEX idx_vendors_city         ON vendors(city);
CREATE INDEX idx_vendors_category     ON vendors(category);
CREATE INDEX idx_vendors_source       ON vendors(source);
CREATE INDEX idx_events_org           ON events(org_id);
CREATE INDEX idx_events_status        ON events(status);
CREATE INDEX idx_outreach_event       ON outreach(event_id);
CREATE INDEX idx_outreach_status      ON outreach(status);
CREATE INDEX idx_quotes_event         ON quotes(event_id);
CREATE INDEX idx_quotes_vendor        ON quotes(vendor_id);
CREATE INDEX idx_quotes_confidence    ON quotes(confidence_score);
CREATE INDEX idx_shortlist_items      ON shortlist_items(shortlist_id);
CREATE INDEX idx_experiments          ON experiments(assumption_id);