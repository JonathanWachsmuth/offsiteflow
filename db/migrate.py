# db/migrate.py
# ─────────────────────────────────────────────────────────────
# Migration runner — applies pending SQL migrations in order.
#
# Usage:
#   python3 -m db.migrate          # apply all pending migrations
#   python3 -m db.migrate --status # show migration state
# ─────────────────────────────────────────────────────────────

import os
import sys
import sqlite3
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_PATH

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def ensure_migrations_table(conn: sqlite3.Connection):
    """Creates the schema_migrations tracking table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id         TEXT PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def get_applied(conn: sqlite3.Connection) -> set:
    """Returns the set of already-applied migration IDs."""
    rows = conn.execute(
        "SELECT id FROM schema_migrations"
    ).fetchall()
    return {row[0] for row in rows}


def get_pending(applied: set) -> list:
    """
    Returns migration filenames not yet applied, sorted by filename.
    Convention: NNN_description.sql where NNN is a zero-padded number.
    """
    files = sorted(
        f for f in os.listdir(MIGRATIONS_DIR)
        if f.endswith(".sql")
    )
    return [f for f in files if f not in applied]


def apply_migration(conn: sqlite3.Connection, filename: str):
    """Reads and executes a single migration file."""
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, "r") as f:
        sql = f.read()

    conn.executescript(sql)
    conn.execute(
        "INSERT INTO schema_migrations (id) VALUES (?)", (filename,)
    )
    conn.commit()
    logger.info("Applied migration: %s", filename)
    print(f"  ✓ {filename}")


def run(db_path: str = None) -> int:
    """
    Applies all pending migrations.
    Returns number of migrations applied.
    """
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    conn = sqlite3.connect(path)
    ensure_migrations_table(conn)

    applied = get_applied(conn)
    pending = get_pending(applied)

    if not pending:
        print("  No pending migrations.")
        conn.close()
        return 0

    print(f"  Applying {len(pending)} migration(s)...")
    for filename in pending:
        apply_migration(conn, filename)

    conn.close()
    return len(pending)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="OffsiteFlow DB migrator")
    parser.add_argument(
        "--status", action="store_true",
        help="Show applied and pending migrations without running"
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_migrations_table(conn)
    applied = get_applied(conn)
    pending = get_pending(applied)
    conn.close()

    if args.status:
        print(f"\nApplied ({len(applied)}):")
        for m in sorted(applied):
            print(f"  ✓ {m}")
        print(f"\nPending ({len(pending)}):")
        for m in pending:
            print(f"  · {m}")
    else:
        print(f"\n{'='*55}")
        print(f"  OffsiteFlow DB Migration")
        print(f"{'='*55}")
        n = run()
        print(f"\n  Done. {n} migration(s) applied.")
        print(f"{'='*55}\n")
