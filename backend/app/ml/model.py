from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ml.preprocessing import preprocess_text
from app.ml.skill_extractor import extract_skills
from app.ml.utils import default_skill_dictionary, normalize_skill_set


@dataclass(frozen=True)
class AnalyzeResult:
    match_score: float
    resume_skills: list[str]
    jd_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    explanation: str


def _split_jd_sections(jd_text: str) -> tuple[str, str]:
    """
    Split JD into must-have and nice-to-have sections when headings are present.
    Falls back to treating the full JD as must-have.
    """
    text = jd_text or ""
    nice_match = re.search(r"nice\s*to\s*have\s*:", text, flags=re.IGNORECASE)
    if not nice_match:
        return text, ""
    must_part = text[: nice_match.start()]
    nice_part = text[nice_match.end() :]
    return must_part, nice_part


def _raw_tfidf_similarity(resume_clean: str, jd_clean: str) -> float:
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    tfidf = vectorizer.fit_transform([resume_clean, jd_clean])
    return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])


def analyze(
    resume_text: str,
    jd_text: str,
    skill_dictionary: list[str] | None = None,
    similarity_reference: dict[str, float] | None = None,
) -> AnalyzeResult:
    skills = skill_dictionary or default_skill_dictionary()

    resume_clean = preprocess_text(resume_text)
    jd_clean = preprocess_text(jd_text)

    sim = _raw_tfidf_similarity(resume_clean, jd_clean)
    if similarity_reference:
        ref_avg = max(0.01, float(similarity_reference.get("avg", 0.01)))
        ref_max = max(ref_avg, float(similarity_reference.get("max", ref_avg)))
        denom = max(ref_avg, ref_max * 0.75, 0.08)
        sim_calibrated = float(np.clip(sim / denom, 0.0, 1.0))
    else:
        # Fallback for single-resume inference when dataset context is unavailable.
        sim_calibrated = float(np.clip(sim / 0.12, 0.0, 1.0))

    resume_skills = extract_skills(resume_text, skills)
    jd_skills = extract_skills(jd_text, skills)

    resume_set = {s.lower() for s in resume_skills}

    must_text, nice_text = _split_jd_sections(jd_text)
    must_skills = extract_skills(must_text, skills) if must_text.strip() else []
    nice_skills = extract_skills(nice_text, skills) if nice_text.strip() else []

    # If no sectioned extraction found, fallback to all JD skills as must-have.
    if not must_skills and not nice_skills:
        must_skills = jd_skills

    must_set = {s.lower() for s in must_skills}
    nice_set = {s.lower() for s in nice_skills if s.lower() not in must_set}
    jd_set = must_set.union(nice_set)

    must_overlap = len(resume_set.intersection(must_set))
    nice_overlap = len(resume_set.intersection(nice_set))
    must_weight = 1.0
    nice_weight = 0.5
    weighted_total = (must_weight * len(must_set)) + (nice_weight * len(nice_set))
    weighted_overlap = (must_weight * must_overlap) + (nice_weight * nice_overlap)
    coverage = (weighted_overlap / weighted_total) if weighted_total > 0 else 0.0
    overlap = must_overlap + nice_overlap

    # ATS score blend: 70% calibrated TF-IDF similarity + 30% skill match coverage.
    score = (0.7 * sim_calibrated + 0.3 * coverage) * 100.0
    score = float(np.clip(score, 0.0, 100.0))

    missing = normalize_skill_set([s for s in jd_skills if s.lower() not in resume_set])
    suggestions = generate_suggestions(missing)

    matched_skills = normalize_skill_set([s for s in jd_skills if s.lower() in resume_set])
    explanation = (
        f"TF-IDF similarity: {sim*100:.1f}% (normalized: {sim_calibrated*100:.1f}%). "
        f"Matched skills: {len(matched_skills)}/{len(jd_set)} ({', '.join(matched_skills[:8]) or 'none'}). "
        f"Must-have matched: {must_overlap}/{len(must_set)}; Nice-to-have matched: {nice_overlap}/{len(nice_set)}. "
        f"Missing skills: {len(missing)} ({', '.join(missing[:8]) or 'none'}). "
        "Final ATS score = 70% TF-IDF + 30% skill match. "
        "Improve score by adding missing must-have skills with concrete project bullets."
    )

    return AnalyzeResult(
        match_score=round(score, 2),
        resume_skills=resume_skills,
        jd_skills=jd_skills,
        missing_skills=missing,
        suggestions=suggestions,
        explanation=explanation,
    )


def estimate_similarity_reference(resume_texts: list[str], jd_text: str) -> dict[str, float]:
    jd_clean = preprocess_text(jd_text)
    sims: list[float] = []
    for text in resume_texts:
        sim = _raw_tfidf_similarity(preprocess_text(text), jd_clean)
        sims.append(sim)
    if not sims:
        return {"avg": 0.1, "max": 0.1}
    return {"avg": float(np.mean(sims)), "max": float(np.max(sims))}


def generate_suggestions(missing_skills: list[str]) -> list[str]:
    out: list[str] = []
    for s in missing_skills[:10]:
        out.append(
            f"Add “{s}” to your Skills section if you have experience, and back it up with 1–2 bullets in a relevant project."
        )
    if missing_skills:
        out.append(
            "Mirror the job description language (tools, frameworks, and keywords) where truthful—ATS systems reward exact matches."
        )
    return out[:12]

