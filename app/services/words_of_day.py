"""Word-of-the-day service — picks a deterministic word for each user per day.

Deterministic means: both you and Nwety see the same word all day if you open
the app multiple times, but it rotates at midnight. No randomness surprises.
"""
import json
from datetime import date
from pathlib import Path

from app.schemas.words import WordOfTheDay

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "word_lists"


def _load(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def word_for_today(user_language: str) -> WordOfTheDay:
    """Return the word-of-the-day for a user, based on their native language.

    The user's native language determines which wordlist we pull from —
    we want to teach them the *other* language.
    """
    if user_language == "pt":
        # Portuguese native speaker → learn English
        words = _load("en_for_nwety.json")
        word_language = "en"
    else:
        # English native speaker → learn Portuguese
        words = _load("pt_for_you.json")
        word_language = "pt"

    # Deterministic daily rotation — same word all day, new word tomorrow
    index = date.today().toordinal() % len(words)
    entry = words[index]

    return WordOfTheDay(
        word=entry["word"],
        language=word_language,
        translation=entry["translation"],
        pronunciation_hint=entry.get("pronunciation_hint"),
        example_sentence=entry.get("example_sentence"),
        example_translation=entry.get("example_translation"),
        theme=entry.get("theme"),
    )