from __future__ import annotations

import logging
from functools import lru_cache

import argostranslate.package
import argostranslate.translate
import spacy
from spacy.language import Language

log = logging.getLogger(__name__)


_nlp_models: dict[str, Language] = {
    "en": spacy.load("en_core_web_sm"),
    "pt": spacy.load("pt_core_news_sm"),
}

POS_LABELS_EN = {
    "NOUN": "noun", "VERB": "verb", "ADJ": "adjective", "ADV": "adverb",
    "PRON": "pronoun", "DET": "determiner", "ADP": "preposition",
    "CONJ": "conjunction", "CCONJ": "conjunction", "SCONJ": "conjunction",
    "INTJ": "interjection", "NUM": "number", "PART": "particle",
    "AUX": "auxiliary verb", "PROPN": "proper noun", "PUNCT": "punctuation",
    "SYM": "symbol", "X": "other", "SPACE": "space",
}
POS_LABELS_PT = {
    "NOUN": "substantivo", "VERB": "verbo", "ADJ": "adjetivo", "ADV": "advérbio",
    "PRON": "pronome", "DET": "determinante", "ADP": "preposição",
    "CONJ": "conjunção", "CCONJ": "conjunção", "SCONJ": "conjunção",
    "INTJ": "interjeição", "NUM": "número", "PART": "partícula",
    "AUX": "verbo auxiliar", "PROPN": "nome próprio", "PUNCT": "pontuação",
    "SYM": "símbolo", "X": "outro", "SPACE": "espaço",
}

def _ensure_argos_packages() -> None:
    """Install the en↔pt language packs if they aren't already.

    Runs once at module import. On Render's fresh filesystem this triggers a
    one-time download (~200 MB). On subsequent starts it's instant.
    """
    installed = {
        (p.from_code, p.to_code)
        for p in argostranslate.package.get_installed_packages()
    }
    needed = {("en", "pt"), ("pt", "en")}
    missing = needed - installed
    if not missing:
        return

    log.info("Installing missing Argos language packs: %s", missing)
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    for pkg in available:
        if (pkg.from_code, pkg.to_code) in missing:
            path = pkg.download()
            argostranslate.package.install_from_path(path)
            log.info("Installed %s -> %s", pkg.from_code, pkg.to_code)


_ensure_argos_packages()

@lru_cache(maxsize=5000)
def _translate_cached(text: str, from_code: str, to_code: str) -> str:
    return argostranslate.translate.translate(text, from_code, to_code)


def translate(text: str, from_code: str, to_code: str) -> str:
    """Translate text between 'en' and 'pt'. Results cached in memory."""
    if from_code == to_code:
        return text
    return _translate_cached(text, from_code, to_code)


def break_down(text: str, language: str) -> list[dict]:
    """Split text into tokens with linguistic info for learning."""
    nlp = _nlp_models.get(language)
    if nlp is None:
        return []

    other_language = "pt" if language == "en" else "en"
    pos_labels = POS_LABELS_EN if language == "en" else POS_LABELS_PT

    doc = nlp(text)
    tokens = []
    for tok in doc:
        if tok.is_space:
            continue
        if tok.is_punct:
            tokens.append({
                "word": tok.text, "lemma": tok.text,
                "pos": pos_labels.get(tok.pos_, tok.pos_.lower()),
                "translation": tok.text, "is_punct": True,
            })
            continue

        word_translation = translate(tok.lemma_.lower(), language, other_language)
        tokens.append({
            "word": tok.text, "lemma": tok.lemma_.lower(),
            "pos": pos_labels.get(tok.pos_, tok.pos_.lower()),
            "translation": word_translation, "is_punct": False,
        })
    return tokens


def process_message(text: str, from_language: str) -> dict:
    """Kept for backwards compatibility — not used by the chat router anymore."""
    to_language = "pt" if from_language == "en" else "en"
    translated = translate(text, from_language, to_language)
    return {
        "original_text": text,
        "original_language": from_language,
        "translated_text": translated,
        "translated_language": to_language,
        "breakdown_original": break_down(text, from_language),
        "breakdown_translation": break_down(translated, to_language),
    }