from __future__ import annotations

import json
from pathlib import Path

from ml.dataset_loader import extract_resume_text, load_all_resumes, prepare_for_ranking


def main() -> None:
    dataset = Path(r"C:\Users\Geethanjali\Downloads\archive (5)\Resumes")
    resumes = load_all_resumes(dataset)

    pdf = sum(1 for p in resumes if p.suffix.lower() == ".pdf")
    docx = sum(1 for p in resumes if p.suffix.lower() == ".docx")

    jd = Path("data/sample_jd.txt").read_text(encoding="utf-8")

    file_errors: list[dict[str, str]] = []
    for p in resumes:
        try:
            _ = extract_resume_text(p)
        except Exception as e:  # pragma: no cover - runtime verification helper
            file_errors.append({"file": str(p), "error": str(e)})

    ranked = prepare_for_ranking(dataset, jd)
    top10 = [
        {
            "rank": i + 1,
            "filename": r["filename"],
            "match_score": r["match_score"],
            "missing_skills": r["missing_skills"],
        }
        for i, r in enumerate(ranked[:10])
    ]

    report = {
        "dataset_path": str(dataset),
        "total_resumes_detected": len(resumes),
        "pdf_files": pdf,
        "docx_files": docx,
        "top_10": top10,
        "file_reading_errors": file_errors,
        "file_reading_errors_count": len(file_errors),
    }
    Path("data/verification_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
