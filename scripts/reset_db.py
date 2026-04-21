"""Nuke the database and let the app re-seed it on next startup.

Useful if you change the User or Message schema. Run this, then restart the
app — lifespan() will recreate tables and seed the two users.
"""
from pathlib import Path

DB = Path(__file__).parent.parent / "nwety.db"
if DB.exists():
    DB.unlink()
    print(f"Deleted {DB.name}")
else:
    print(f"{DB.name} does not exist — nothing to do")