from __future__ import annotations

import re
from functools import lru_cache

import spacy
from spacy.language import Language
from spacy.pipeline import EntityRuler

from app.ml.utils import canonicalize_skill, normalize_skill_set, skill_aliases


@lru_cache(maxsize=1)
def _nlp() -> Language:
    """
    Uses a small English model if available, otherwise falls back to a blank pipeline.
    We only need tokenization + EntityRuler patterns here.
    """
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = spacy.blank("en")

    if "ner" in nlp.pipe_names:
        # We prefer our ruler signals; keep NER if present.
        pass

    if "entity_ruler" not in nlp.pipe_names:
        nlp.add_pipe("entity_ruler", before="ner" if "ner" in nlp.pipe_names else None)
    return nlp


def _build_ruler(skills: list[str]) -> EntityRuler:
    nlp = _nlp()
    ruler = nlp.get_pipe("entity_ruler")
    ruler.clear()

    patterns = []
    for s in skills:
        s = s.strip()
        if not s:
            continue
        # Treat each skill as a phrase pattern.
        patterns.append({"label": "SKILL", "pattern": s})
    ruler.add_patterns(patterns)
    return ruler


def extract_skills(text: str, skill_dictionary: list[str]) -> list[str]:
    raw = text or ""
    if not raw.strip():
        return []

    # Ensure ruler patterns are current for this dictionary.
    _build_ruler(skill_dictionary)

    nlp = _nlp()
    doc = nlp(raw)

    found: list[str] = []
    for ent in doc.ents:
        if ent.label_ == "SKILL":
            found.append(canonicalize_skill(ent.text))

    # Curated dictionary fallback with regex boundaries for robust JD matching.
    hay = re.sub(r"\s+", " ", raw.lower())
    aliases = skill_aliases()
    expanded_terms: list[tuple[str, str]] = [(s, s) for s in skill_dictionary]
    expanded_terms.extend((alias, canonical) for alias, canonical in aliases.items())
    for term, canonical in expanded_terms:
        normalized = re.sub(r"\s+", " ", term.lower().strip())
        if not normalized:
            continue
        # For alphabetic phrases use word boundaries; for symbolic skills (e.g., C++, CI/CD)
        # use escaped phrase match so punctuation is still discoverable.
        if re.search(r"[a-z0-9]", normalized) and re.search(r"[a-z]", normalized):
            pattern = rf"(?<!\w){re.escape(normalized)}(?!\w)"
        else:
            pattern = re.escape(normalized)
        if re.search(pattern, hay, flags=re.IGNORECASE):
            found.append(canonicalize_skill(canonical))

    # Partial phrase matching: useful for variants like "machine-learning", "restful api".
    for skill in skill_dictionary:
        canonical = canonicalize_skill(skill)
        key = re.sub(r"[^a-z0-9]+", " ", canonical.lower()).strip()
        if not key:
            continue
        tokens = [t for t in key.split() if len(t) > 1]
        if tokens and all(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", hay) for t in tokens):
            found.append(canonical)

    return normalize_skill_set([canonicalize_skill(s) for s in found])

