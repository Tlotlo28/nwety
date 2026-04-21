"""Word-of-the-day service with localized labels."""
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
    if user_language == "pt":
        words = _load("en_for_nwety.json")
        word_language = "en"
    else:
        words = _load("pt_for_you.json")
        word_language = "pt"

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