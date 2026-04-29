from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.ml.model import analyze, estimate_similarity_reference
from app.ml.preprocessing import preprocess_text
from app.services.document_parser import UnsupportedFileTypeError, extract_text_from_upload


SUPPORTED_RESUME_EXTENSIONS = {".pdf", ".docx"}


@dataclass(frozen=True)
class ResumeDatasetItem:
    filename: str
    path: str
    text: str
    preprocessed_text: str


def load_all_resumes(dataset_dir: str | Path) -> list[Path]:
    """
    Discover all supported resumes recursively from a dataset folder.
    """
    root = Path(dataset_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Dataset directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Dataset path is not a directory: {root}")

    resumes = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_RESUME_EXTENSIONS
    ]
    return sorted(resumes, key=lambda p: p.name.lower())


def extract_resume_text(file_path: str | Path) -> str:
    """
    Extract plain text from one resume (PDF/DOCX).
    """
    path = Path(file_path).expanduser().resolve()
    if path.suffix.lower() not in SUPPORTED_RESUME_EXTENSIONS:
        raise UnsupportedFileTypeError("Only PDF and DOCX files are supported.")

    content = path.read_bytes()
    return extract_text_from_upload(path.name, content)


def preprocess_dataset(resume_paths: list[str | Path]) -> list[ResumeDatasetItem]:
    """
    Extract and preprocess all resumes using existing preprocessing logic.
    """
    dataset: list[ResumeDatasetItem] = []
    for p in resume_paths:
        path = Path(p).expanduser().resolve()
        text = extract_resume_text(path)
        preprocessed_text = preprocess_text(text)
        dataset.append(
            ResumeDatasetItem(
                filename=path.name,
                path=str(path),
                text=text,
                preprocessed_text=preprocessed_text,
            )
        )
    return dataset


def prepare_for_ranking(
    dataset_dir: str | Path,
    jd_text: str,
    skill_dictionary: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Compare all resumes against one JD and return ranked results.

    Reuses existing analysis logic (preprocess + TF-IDF/cosine + skill gap analysis).
    """
    if not jd_text or not jd_text.strip():
        raise ValueError("Job description text is required.")

    resume_paths = load_all_resumes(dataset_dir)
    processed_items = preprocess_dataset(resume_paths)
    similarity_reference = estimate_similarity_reference([item.text for item in processed_items], jd_text)

    ranked: list[dict[str, Any]] = []
    for item in processed_items:
        # analyze() already uses existing preprocessing + TF-IDF/cosine + skills logic.
        result = analyze(
            resume_text=item.text,
            jd_text=jd_text,
            skill_dictionary=skill_dictionary,
            similarity_reference=similarity_reference,
        )
        ranked.append(
            {
                "filename": item.filename,
                "path": item.path,
                "match_score": result.match_score,
                "resume_skills": result.resume_skills,
                "jd_skills": result.jd_skills,
                "missing_skills": result.missing_skills,
                "suggestions": result.suggestions,
                "explanation": result.explanation,
            }
        )

    ranked.sort(key=lambda x: float(x["match_score"]), reverse=True)
    return ranked
