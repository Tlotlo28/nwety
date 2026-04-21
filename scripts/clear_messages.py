"""Clear all chat messages. Users and saved words are untouched."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent / "nwety.db"

with sqlite3.connect(DB) as conn:
    deleted = conn.execute("DELETE FROM messages").rowcount
    # sqlite_sequence only exists if an AUTOINCREMENT table has been written to.
    # Reset the counter if it's there; harmless to skip if it isn't.
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
    ).fetchone()
    if exists:
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'messages'")
    conn.commit()

print(f"Cleared {deleted} messages from {DB.name}")