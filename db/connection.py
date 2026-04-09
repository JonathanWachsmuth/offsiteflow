# db/connection.py
# ─────────────────────────────────────────────────────────────
# Context manager for SQLite connections.
# Use everywhere instead of sqlite3.connect() directly.
#
# Usage:
#   from db.connection import get_db
#
#   with get_db() as conn:
#       conn.execute("SELECT ...")
#
# Commits on clean exit, rolls back on exception, always closes.
# ─────────────────────────────────────────────────────────────

from contextlib import contextmanager
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_PATH


@contextmanager
def get_db(path: str = None):
    """
    Yields an open SQLite connection with row_factory set.
    Commits on success, rolls back on exception, always closes.

    Args:
        path: override DB path (used in tests). Defaults to settings.DB_PATH.
    """
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
