# config/settings.py
# ─────────────────────────────────────────────────────────────
# Single source of truth for all configuration.
# All values loaded from .env — no hardcoded secrets anywhere.
# ─────────────────────────────────────────────────────────────

from dotenv import load_dotenv
import os

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY    = os.getenv("GOOGLE_API_KEY")
TALLY_FORM_URL    = os.getenv("TALLY_FORM_URL", "https://tally.so/r/PdY7Je")

# ── Email / SMTP ──────────────────────────────────────────────
SMTP_EMAIL    = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587

# ── Database (SQLite — local fallback / migration source) ─────
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "vendors.db"
)

# ── Supabase ──────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kyrodpcviaximcbuzykf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ── File paths ────────────────────────────────────────────────
RAW_SCRAPED_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "scraped"
)
MANUAL_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "manual", "vendors_seed.csv"
)
SHORTLIST_OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "output", "shortlists"
)

# ── LLM ───────────────────────────────────────────────────────
LLM_MODEL      = "claude-sonnet-4-20250514"
LLM_MAX_TOKENS = 1000

# ── Pipeline ──────────────────────────────────────────────────
DEFAULT_CITY       = "London"
TOP_N_PER_CATEGORY = 5
MAX_CANDIDATES     = 30
REFRESH_DAYS       = 30

# ── Thresholds (from validated experiments) ───────────────────
A1_MIN_VENDORS       = 200
A2_MIN_EMAIL_RATE    = 0.60
A3_MIN_RESPONSE_RATE = 0.50
A5_MIN_ACCURACY      = 0.80
