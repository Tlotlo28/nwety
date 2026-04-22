"""Translation and language breakdown service.

Tuned to fit Render's 512 MB ceiling:
  - Only ONE spaCy model loaded at a time (swap on language change)
  - Argos translator with cached results
  - Per-word breakdown uses a single batched call
  - Optional contextual hint to disambiguate verbs (love -> amar, not amor)
"""
from __future__ import annotations

import gc
import logging
import threading
from functools import lru_cache

import argostranslate.package
import argostranslate.translate

log = logging.getLogger(__name__)


def _ensure_argos_packages() -> None:
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


_ensure_argos_packages()

# Single-slot spaCy model cache. We keep at most one loaded at a time.
_nlp_lock = threading.Lock()
_current_nlp = {"language": None, "model": None}
_DISABLED_PIPES = ["ner", "parser", "attribute_ruler"]


def _get_nlp(language: str):
    """Return the spaCy model for `language`, swapping in if needed."""
    with _nlp_lock:
        if _current_nlp["language"] == language and _current_nlp["model"] is not None:
            return _current_nlp["model"]

        # Drop the previous model (if any) before loading the new one
        if _current_nlp["model"] is not None:
            log.info("Unloading spaCy %s to make room for %s",
                     _current_nlp["language"], language)
            _current_nlp["model"] = None
            _current_nlp["language"] = None
            gc.collect()

        import spacy  # local import keeps it out of memory until first use
        model_name = "en_core_web_sm" if language == "en" else "pt_core_news_sm"
        log.info("Loading spaCy model %s", model_name)
        _current_nlp["model"] = spacy.load(model_name, disable=_DISABLED_PIPES)
        _current_nlp["language"] = language
        return _current_nlp["model"]


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

_SEP = "\n|||\n"


@lru_cache(maxsize=3000)
def _translate_cached(text: str, from_code: str, to_code: str) -> str:
    return argostranslate.translate.translate(text, from_code, to_code)


def translate(text: str, from_code: str, to_code: str) -> str:
    if from_code == to_code:
        return text
    return _translate_cached(text, from_code, to_code)


def _batch_translate_words(words: list[str], from_code: str, to_code: str) -> list[str]:
    if not words:
        return []
    if from_code == to_code:
        return list(words)

    joined = _SEP.join(words)
    try:
        translated_joined = argostranslate.translate.translate(joined, from_code, to_code)
        parts = translated_joined.split(_SEP)
    except Exception as exc:  # noqa: BLE001
        log.warning("Batched translation failed: %s", exc)
        parts = [translate(w, from_code, to_code) for w in words]

    if len(parts) != len(words):
        parts = [translate(w, from_code, to_code) for w in words]

    return [(p.strip() if p else words[i]) for i, p in enumerate(parts)]


def _contextualise(word: str, pos: str, language: str) -> str:
    """Add a tiny grammatical hint so verbs translate as verbs, not nouns."""
    if language == "en" and pos in ("verb", "auxiliary verb"):
        return f"to {word}"
    return word


def _strip_context(translated: str, original_context: str, language: str) -> str:
    """Strip the contextual prefix back out of the translation."""
    if language == "en" and original_context.startswith("to "):
        for prefix in ("para ", "a ", "de "):
            if translated.lower().startswith(prefix):
                return translated[len(prefix):].strip()
    return translated.strip()


def break_down(text: str, language: str) -> list[dict]:
    nlp = _get_nlp(language)
    other_language = "pt" if language == "en" else "en"
    pos_labels = POS_LABELS_EN if language == "en" else POS_LABELS_PT

    doc = nlp(text)
    raw_tokens = []
    contexts: list[str] = []
    for tok in doc:
        if tok.is_space:
            continue
        if tok.is_punct:
            raw_tokens.append({
                "word": tok.text, "lemma": tok.text,
                "pos": pos_labels.get(tok.pos_, tok.pos_.lower()),
                "translation": tok.text, "is_punct": True,
            })
            continue
        lemma = tok.lemma_.lower()
        pos_label = pos_labels.get(tok.pos_, tok.pos_.lower())
        raw_tokens.append({
            "word": tok.text, "lemma": lemma, "pos": pos_label,
            "translation": None, "is_punct": False,
        })
        contexts.append(_contextualise(lemma, pos_label, language))

    translations = _batch_translate_words(contexts, language, other_language)
    cleaned = [
        _strip_context(t, c, language)
        for t, c in zip(translations, contexts)
    ]

    t_iter = iter(cleaned)
    for tok in raw_tokens:
        if not tok["is_punct"]:
            tok["translation"] = next(t_iter, tok["lemma"])

    del doc
    gc.collect()
    return raw_tokens


def process_message(text: str, from_language: str) -> dict:
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