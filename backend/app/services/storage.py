from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database.db"
RESUMES_DIR = BASE_DIR / "data" / "resumes"
FALLBACK_DATASET_DIR = Path(
    os.getenv("RESUME_DATASET_DIR", r"C:\Users\Geethanjali\Downloads\archive (5)\Resumes")
)
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                match_score REAL NOT NULL,
                resume_skills TEXT NOT NULL,
                jd_skills TEXT NOT NULL,
                missing_skills TEXT NOT NULL,
                suggestions TEXT NOT NULL,
                explanation TEXT NOT NULL,
                jd_text TEXT NOT NULL,
                analyzed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_uploaded_resume(filename: str, content: bytes) -> str:
    """
    Persist uploaded resume under backend/data/resumes and return stored filename.
    """
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)

    raw_name = (filename or "").strip()
    ext = Path(raw_name).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        ext = ".pdf" if ext == "" else ext

    stem = Path(raw_name).stem.strip() or "resume"
    safe_stem = "".join(ch if ch.isalnum() or ch in ("-", "_", " ") else "_" for ch in stem).strip()
    safe_stem = safe_stem or "resume"

    candidate = RESUMES_DIR / f"{safe_stem}{ext}"
    if candidate.exists():
        candidate = RESUMES_DIR / f"{safe_stem}-{uuid4().hex[:8]}{ext}"

    candidate.write_bytes(content)
    return candidate.name


def save_analysis_record(
    *,
    filename: str,
    match_score: float,
    resume_skills: list[str],
    jd_skills: list[str],
    missing_skills: list[str],
    suggestions: list[str],
    explanation: str,
    jd_text: str,
) -> None:
    file_type = Path(filename).suffix.lower().lstrip(".")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO analysis_history (
                filename,
                file_type,
                match_score,
                resume_skills,
                jd_skills,
                missing_skills,
                suggestions,
                explanation,
                jd_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                file_type,
                match_score,
                json.dumps(resume_skills),
                json.dumps(jd_skills),
                json.dumps(missing_skills),
                json.dumps(suggestions),
                explanation,
                jd_text,
            ),
        )
        conn.commit()


def get_analysis_history(limit: int = 200) -> list[dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                id,
                filename,
                file_type,
                match_score,
                resume_skills,
                jd_skills,
                missing_skills,
                suggestions,
                explanation,
                jd_text,
                analyzed_at
            FROM analysis_history
            ORDER BY datetime(analyzed_at) DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": row["id"],
                "filename": row["filename"],
                "file_type": row["file_type"],
                "match_score": float(row["match_score"]),
                "resume_skills": json.loads(row["resume_skills"]),
                "jd_skills": json.loads(row["jd_skills"]),
                "missing_skills": json.loads(row["missing_skills"]),
                "suggestions": json.loads(row["suggestions"]),
                "explanation": row["explanation"],
                "jd_text": row["jd_text"],
                "timestamp": row["analyzed_at"],
            }
        )
    return out


def get_resume_library() -> list[dict[str, Any]]:
    files = _collect_resume_files()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        latest = conn.execute(
            """
            SELECT filename, MAX(datetime(analyzed_at)) AS last_analyzed_date
            FROM analysis_history
            GROUP BY filename
            """
        ).fetchall()
        latest_map = {row["filename"]: row["last_analyzed_date"] for row in latest}

        scores = conn.execute(
            """
            SELECT a.filename, a.match_score
            FROM analysis_history a
            JOIN (
                SELECT filename, MAX(datetime(analyzed_at)) AS max_dt
                FROM analysis_history
                GROUP BY filename
            ) b
            ON a.filename = b.filename
            AND datetime(a.analyzed_at) = b.max_dt
            """
        ).fetchall()
        score_map = {row["filename"]: float(row["match_score"]) for row in scores}

    out: list[dict[str, Any]] = []
    for file_path in files:
        name = file_path.name
        out.append(
            {
                "resume_name": name,
                "file_type": file_path.suffix.lower().lstrip("."),
                "last_analyzed_date": latest_map.get(name),
                "latest_match_score": score_map.get(name),
            }
        )
    return out


def _collect_resume_files() -> list[Path]:
    """
    Load resumes from app storage folder and fallback dataset folder.
    """
    files: list[Path] = []
    seen_paths: set[str] = set()

    sources: list[Path] = [RESUMES_DIR]
    if FALLBACK_DATASET_DIR.exists():
        sources.append(FALLBACK_DATASET_DIR)

    for source in sources:
        for p in source.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            key = str(p.resolve()).lower()
            if key in seen_paths:
                continue
            seen_paths.add(key)
            files.append(p)

    files.sort(key=lambda p: p.name.lower())
    return files
