"""TV shows and basic language tips loaded from curated JSON."""
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent.parent / "data" / "content" / "library.json"


def _load() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_library_for_user(user_language: str) -> dict:
    """Return shows and tips relevant to a user based on their native language.

    A Portuguese speaker gets English-learning shows and English tips; an English
    speaker gets Portuguese-learning shows and Portuguese tips.
    """
    data = _load()
    if user_language == "pt":
        return {
            "shows": data["shows_for_nwety"],
            "tips": data["tips_english"],
            "learning_language": "en",
        }
    return {
        "shows": data["shows_for_you"],
        "tips": data["tips_portuguese"],
        "learning_language": "pt",
    }