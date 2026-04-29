from __future__ import annotations

from pathlib import Path

from app.ml.model import analyze, estimate_similarity_reference
from ml.dataset_loader import extract_resume_text, load_all_resumes, prepare_for_ranking


def main() -> None:
    dataset_dir = Path("data/resumes")
    jd_path = Path("data/sample_jd.txt")
    target_name = "Venkata_Sr_PHP_Developer.docx"

    jd_text = jd_path.read_text(encoding="utf-8")
    all_paths = load_all_resumes(dataset_dir)
    by_name = {p.name: p for p in all_paths}
    if target_name not in by_name:
        raise FileNotFoundError(f"Target resume not found in dataset: {target_name}")
    target_path = by_name[target_name]

    ranked = prepare_for_ranking(dataset_dir, jd_text)
    ranked_row = next((r for r in ranked if r["filename"] == target_name), None)
    if ranked_row is None:
        raise RuntimeError(f"Target resume not found in ranked output: {target_name}")

    reference_texts = [extract_resume_text(p) for p in all_paths if p.exists()]
    upload_resume_text = extract_resume_text(target_path)
    similarity_reference = estimate_similarity_reference(reference_texts + [upload_resume_text], jd_text)
    upload_result = analyze(
        resume_text=upload_resume_text,
        jd_text=jd_text,
        similarity_reference=similarity_reference,
    )

    print("\n=== ATS Flow Debug Comparison ===")
    print(f"Resume: {target_name}")
    print(f"Dataset flow text length: {len(extract_resume_text(target_path))}")
    print(f"Upload flow text length: {len(upload_resume_text)}")
    print(f"Dataset flow skills: {len(ranked_row['resume_skills'])} -> {ranked_row['resume_skills'][:12]}")
    print(f"Upload flow skills: {len(upload_result.resume_skills)} -> {upload_result.resume_skills[:12]}")
    print(f"Dataset flow explanation: {ranked_row['explanation']}")
    print(f"Upload flow explanation: {upload_result.explanation}")
    print(f"Dataset flow ATS score: {ranked_row['match_score']}")
    print(f"Upload flow ATS score: {upload_result.match_score}")


if __name__ == "__main__":
    main()

