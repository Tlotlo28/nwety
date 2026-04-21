"""TV shows, language tips, and localized UI labels."""
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent.parent / "data" / "content" / "library.json"

# UI labels per user's native language — English speakers see English labels,
# Portuguese speakers see Portuguese labels.
UI_LABELS = {
    "en": {
        "word_of_the_day": "Word of the day",
        "hear_it": "Hear it",
        "hear_example": "Hear example",
        "watch_and_learn": "Watch & learn",
        "watch_section_heading": "TV shows & channels",
        "watch_section_subtitle": "When you can't chat, watch.",
        "tips_label": "Quick tips",
        "tips_heading": "{language} basics",
        "learning_language_name": {"en": "English", "pt": "Portuguese"},
        "level_label": "Level",
        "where_label": "Where",
    },
    "pt": {
        "word_of_the_day": "Palavra do dia",
        "hear_it": "Ouvir",
        "hear_example": "Ouvir exemplo",
        "watch_and_learn": "Ver e aprender",
        "watch_section_heading": "Séries e canais",
        "watch_section_subtitle": "Quando não puderes conversar, vê algo.",
        "tips_label": "Dicas rápidas",
        "tips_heading": "Básicos de {language}",
        "learning_language_name": {"en": "inglês", "pt": "português"},
        "level_label": "Nível",
        "where_label": "Onde",
    },
}


def _load() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_library_for_user(user_language: str) -> dict:
    """Return shows, tips, and UI labels in the user's native language."""
    data = _load()
    labels = UI_LABELS.get(user_language, UI_LABELS["en"])

    if user_language == "pt":
        shows = data["shows_for_nwety_pt"]
        tips = data["tips_english_pt"]
        learning_language = "en"
    else:
        shows = data["shows_for_you"]
        tips = data["tips_portuguese"]
        learning_language = "pt"

    labels_out = {
        **labels,
        "learning_language_display": labels["learning_language_name"][learning_language],
    }
    labels_out["tips_heading"] = labels_out["tips_heading"].format(
        language=labels_out["learning_language_display"]
    )

    return {
        "shows": shows,
        "tips": tips,
        "learning_language": learning_language,
        "labels": labels_out,
    }