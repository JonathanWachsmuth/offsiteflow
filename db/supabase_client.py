# db/supabase_client.py
# ─────────────────────────────────────────────────────────────
# Singleton Supabase client.
# Import `sb` anywhere in the pipeline instead of sqlite3.
#
# Usage:
#   from db.supabase_client import sb
#   rows = sb.table("vendors").select("*").eq("city", "London").execute()
# ─────────────────────────────────────────────────────────────

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# Convenience alias — use `sb` directly
sb = get_supabase()
