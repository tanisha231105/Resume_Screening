from __future__ import annotations

from pathlib import Path

from ml.dataset_loader import extract_resume_text, load_all_resumes, prepare_for_ranking


DATASET_PATH = Path(r"C:\Users\Geethanjali\Downloads\archive (5)\Resumes")
SAMPLE_JD_PATH = Path("data/sample_jd.txt")


def main() -> None:
    if not SAMPLE_JD_PATH.exists():
        raise FileNotFoundError(f"Job description file not found: {SAMPLE_JD_PATH}")

    resumes = load_all_resumes(DATASET_PATH)
    jd_text = SAMPLE_JD_PATH.read_text(encoding="utf-8")

    pdf_count = sum(1 for p in resumes if p.suffix.lower() == ".pdf")
    docx_count = sum(1 for p in resumes if p.suffix.lower() == ".docx")

    file_errors: list[tuple[str, str]] = []
    for resume_path in resumes:
        try:
            _ = extract_resume_text(resume_path)
        except Exception as exc:  # runtime verification utility
            file_errors.append((str(resume_path), str(exc)))

    ranked = prepare_for_ranking(DATASET_PATH, jd_text)
    top_10 = ranked[:10]

    print("\n=== Dataset Verification Report ===")
    print(f"1. Total resumes detected: {len(resumes)}")
    print(f"2. Number of PDF files: {pdf_count}")
    print(f"3. Number of DOCX files: {docx_count}")

    print("\n4-6. Top 10 ranked resumes (match score + missing skills):")
    if not top_10:
        print("No resumes were ranked.")
    else:
        for idx, item in enumerate(top_10, start=1):
            missing = item.get("missing_skills", [])
            missing_text = ", ".join(missing) if missing else "None"
            print(f"{idx}. {item.get('filename', 'unknown')}")
            print(f"   Match score: {item.get('match_score', 'N/A')}")
            print(f"   Missing skills: {missing_text}")

    print("\n7. File reading errors:")
    if not file_errors:
        print("No file reading errors found.")
    else:
        print(f"Total file reading errors: {len(file_errors)}")
        for idx, (file_path, error_msg) in enumerate(file_errors, start=1):
            print(f"{idx}. {file_path}")
            print(f"   Error: {error_msg}")


if __name__ == "__main__":
    main()
