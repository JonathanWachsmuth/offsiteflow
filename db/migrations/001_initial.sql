-- ==============================================
-- OFFSITEFLOW DATABASE SCHEMA
-- Migration 001 — Initial schema
-- Version 1.0 | SQLite
-- ==============================================

PRAGMA foreign_keys = ON;

-- ==============================================
-- ORGANISATIONS
-- The company using OffsiteFlow
-- ==============================================

CREATE TABLE IF NOT EXISTS organisations (
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
-- ==============================================

CREATE TABLE IF NOT EXISTS users (
    id                  TEXT PRIMARY KEY,
    org_id              TEXT NOT NULL REFERENCES organisations(id),
    email               TEXT NOT NULL UNIQUE,
    name                TEXT,
    role                TEXT DEFAULT 'planner',  -- planner / admin / viewer
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- EVENTS
-- ==============================================

CREATE TABLE IF NOT EXISTS events (
    id                  TEXT PRIMARY KEY,
    org_id              TEXT NOT NULL REFERENCES organisations(id),
    created_by          TEXT REFERENCES users(id),
    name                TEXT,
    type                TEXT,
    city                TEXT NOT NULL,
    country             TEXT DEFAULT 'GB',
    date_start          DATE,
    date_end            DATE,
    headcount           INTEGER NOT NULL,
    budget_total        REAL NOT NULL,
    budget_currency     TEXT DEFAULT 'GBP',
    brief_text          TEXT,
    requirements        TEXT,
    status              TEXT DEFAULT 'draft',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_templates (
    id                  TEXT PRIMARY KEY,
    org_id              TEXT REFERENCES organisations(id),
    based_on_event      TEXT REFERENCES events(id),
    name                TEXT,
    default_type        TEXT,
    default_city        TEXT,
    default_budget      REAL,
    default_headcount   INTEGER,
    requirements        TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- VENDORS
-- ==============================================

CREATE TABLE IF NOT EXISTS vendors (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    category            TEXT NOT NULL,
    subcategory         TEXT,
    city                TEXT NOT NULL,
    country             TEXT DEFAULT 'GB',
    address             TEXT,
    capacity_min        INTEGER,
    capacity_max        INTEGER,
    price_from          REAL,
    price_unit          TEXT,
    currency            TEXT DEFAULT 'GBP',
    email               TEXT,
    phone               TEXT,
    website             TEXT,
    contact_form        TEXT,
    description         TEXT,
    amenities           TEXT,
    tags                TEXT,
    sustainability      TEXT,
    lead_time_days      INTEGER,
    cancellation_policy TEXT,
    deposit_required    REAL,
    rating_external     REAL,
    rating_count        INTEGER,
    source              TEXT,
    source_url          TEXT,
    verified            INTEGER DEFAULT 0,
    last_verified       DATE,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendor_contacts (
    id                  TEXT PRIMARY KEY,
    vendor_id           TEXT NOT NULL REFERENCES vendors(id),
    contact_name        TEXT,
    contact_email       TEXT,
    contact_role        TEXT,
    is_primary          INTEGER DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organisation_vendors (
    org_id              TEXT REFERENCES organisations(id),
    vendor_id           TEXT REFERENCES vendors(id),
    preferred           INTEGER DEFAULT 0,
    notes               TEXT,
    PRIMARY KEY (org_id, vendor_id)
);

CREATE TABLE IF NOT EXISTS vendor_reviews (
    id                  TEXT PRIMARY KEY,
    vendor_id           TEXT REFERENCES vendors(id),
    event_id            TEXT REFERENCES events(id),
    rating              INTEGER,
    response_speed_hrs  INTEGER,
    quote_accuracy      INTEGER,
    would_rebook        INTEGER,
    notes               TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- PIPELINE: OUTREACH
-- ==============================================

CREATE TABLE IF NOT EXISTS outreach (
    id                  TEXT PRIMARY KEY,
    event_id            TEXT NOT NULL REFERENCES events(id),
    vendor_id           TEXT NOT NULL REFERENCES vendors(id),
    email_to            TEXT NOT NULL,
    email_subject       TEXT,
    email_body          TEXT,
    sent_at             DATETIME,
    status              TEXT DEFAULT 'pending',
    raw_response        TEXT,
    response_at         DATETIME,
    raw_file_path       TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id                  TEXT PRIMARY KEY,
    outreach_id         TEXT NOT NULL REFERENCES outreach(id),
    direction           TEXT NOT NULL,
    subject             TEXT,
    body                TEXT,
    sent_at             DATETIME,
    raw_file_path       TEXT
);

-- ==============================================
-- PIPELINE: QUOTES
-- ==============================================

CREATE TABLE IF NOT EXISTS quotes (
    id                  TEXT PRIMARY KEY,
    outreach_id         TEXT REFERENCES outreach(id),
    event_id            TEXT NOT NULL REFERENCES events(id),
    vendor_id           TEXT NOT NULL REFERENCES vendors(id),
    version             INTEGER DEFAULT 1,
    parent_quote_id     TEXT REFERENCES quotes(id),
    superseded          INTEGER DEFAULT 0,
    base_price          REAL,
    price_per_head      REAL,
    service_fee         REAL,
    vat_rate            REAL,
    total_estimated     REAL,
    currency            TEXT DEFAULT 'GBP',
    price_unit          TEXT,
    inclusions          TEXT,
    exclusions          TEXT,
    capacity_offered    INTEGER,
    availability        INTEGER,
    confidence_score    REAL,
    extraction_notes    TEXT,
    extracted_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    manually_reviewed   INTEGER DEFAULT 0,
    normalised          INTEGER DEFAULT 0,
    normalisation_notes TEXT,
    status              TEXT DEFAULT 'extracted'
);

-- ==============================================
-- OUTPUT: SHORTLISTS
-- ==============================================

CREATE TABLE IF NOT EXISTS shortlists (
    id                  TEXT PRIMARY KEY,
    event_id            TEXT NOT NULL REFERENCES events(id),
    generated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    status              TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS shortlist_items (
    id                  TEXT PRIMARY KEY,
    shortlist_id        TEXT NOT NULL REFERENCES shortlists(id),
    quote_id            TEXT NOT NULL REFERENCES quotes(id),
    rank                INTEGER,
    rank_score          REAL,
    rank_reason         TEXT,
    selected            INTEGER DEFAULT 0
);

-- ==============================================
-- BUDGET TRACKING
-- ==============================================

CREATE TABLE IF NOT EXISTS budget_entries (
    id                  TEXT PRIMARY KEY,
    event_id            TEXT NOT NULL REFERENCES events(id),
    vendor_id           TEXT REFERENCES vendors(id),
    type                TEXT,
    amount              REAL,
    currency            TEXT DEFAULT 'GBP',
    notes               TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- EXPERIMENT TRACKING
-- ==============================================

CREATE TABLE IF NOT EXISTS experiments (
    id                  TEXT PRIMARY KEY,
    assumption_id       TEXT NOT NULL,
    hypothesis          TEXT,
    method              TEXT,
    min_success         TEXT,
    result              TEXT,
    outcome             TEXT,
    notes               TEXT,
    run_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- INDEXES
-- ==============================================

CREATE INDEX IF NOT EXISTS idx_vendors_city      ON vendors(city);
CREATE INDEX IF NOT EXISTS idx_vendors_category  ON vendors(category);
CREATE INDEX IF NOT EXISTS idx_vendors_source    ON vendors(source);
CREATE INDEX IF NOT EXISTS idx_events_org        ON events(org_id);
CREATE INDEX IF NOT EXISTS idx_events_status     ON events(status);
CREATE INDEX IF NOT EXISTS idx_outreach_event    ON outreach(event_id);
CREATE INDEX IF NOT EXISTS idx_outreach_status   ON outreach(status);
CREATE INDEX IF NOT EXISTS idx_quotes_event      ON quotes(event_id);
CREATE INDEX IF NOT EXISTS idx_quotes_vendor     ON quotes(vendor_id);
CREATE INDEX IF NOT EXISTS idx_quotes_confidence ON quotes(confidence_score);
CREATE INDEX IF NOT EXISTS idx_shortlist_items   ON shortlist_items(shortlist_id);
CREATE INDEX IF NOT EXISTS idx_experiments       ON experiments(assumption_id);
