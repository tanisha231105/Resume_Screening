from __future__ import annotations

import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


_NON_WORD = re.compile(r"[^a-zA-Z0-9\s\+\#\.\-/]")
_MULTI_SPACE = re.compile(r"\s+")


def preprocess_text(text: str) -> str:
    """
    Lightweight preprocessing intended for ATS-style matching:
    lowercase, regex cleanup, stopword removal.
    """
    t = (text or "").lower()
    t = _NON_WORD.sub(" ", t)
    t = _MULTI_SPACE.sub(" ", t).strip()
    if not t:
        return ""

    tokens = [tok for tok in t.split(" ") if tok and tok not in ENGLISH_STOP_WORDS]
    return " ".join(tokens)

