from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.ml.model import analyze, estimate_similarity_reference
from app.schemas import AnalyzeResponse, EvaluationSummaryResponse, HistoryItem, ResumeLibraryItem
from app.services.document_parser import UnsupportedFileTypeError
from app.services.storage import (
    RESUMES_DIR,
    get_analysis_history,
    get_resume_library,
    save_analysis_record,
    save_uploaded_resume,
)
from ml.dataset_loader import extract_resume_text, load_all_resumes
from ml.evaluation import evaluate_dataset

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...),
) -> AnalyzeResponse:
    stored_filename = resume_file.filename or "uploaded_resume"
    try:
        content = await resume_file.read()
        stored_filename = save_uploaded_resume(resume_file.filename or "uploaded_resume", content)
        # Single source of truth: parse exactly as dataset loader parses from disk path.
        stored_path = RESUMES_DIR / stored_filename
        resume_text = extract_resume_text(stored_path)
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to parse resume file.") from e

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text could not be extracted.")
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")

    # Use the same calibrated scoring reference strategy as dataset ranking/verification.
    similarity_reference = None
    try:
        dataset_dir = Path("data/resumes")
        reference_texts: list[str] = []
        if dataset_dir.exists() and dataset_dir.is_dir():
            for resume_path in load_all_resumes(dataset_dir):
                try:
                    text = extract_resume_text(resume_path)
                    if text.strip():
                        reference_texts.append(text)
                except Exception:
                    continue
        # Include currently uploaded resume in the normalization population.
        reference_texts.append(resume_text)
        if len(reference_texts) >= 2:
            similarity_reference = estimate_similarity_reference(reference_texts, jd_text)
    except Exception:
        similarity_reference = None

    result = analyze(
        resume_text=resume_text,
        jd_text=jd_text,
        similarity_reference=similarity_reference,
    )
    logger.info(
        "ATS debug upload: file=%s text_len=%s resume_skills=%s jd_skills=%s score=%s",
        stored_filename,
        len(resume_text),
        len(result.resume_skills),
        len(result.jd_skills),
        result.match_score,
    )
    save_analysis_record(
        filename=stored_filename,
        match_score=result.match_score,
        resume_skills=result.resume_skills,
        jd_skills=result.jd_skills,
        missing_skills=result.missing_skills,
        suggestions=result.suggestions,
        explanation=result.explanation,
        jd_text=jd_text,
    )
    return AnalyzeResponse(**result.__dict__)


@router.get("/resumes", response_model=list[ResumeLibraryItem])
def resumes_endpoint() -> list[ResumeLibraryItem]:
    return [ResumeLibraryItem(**row) for row in get_resume_library()]


@router.get("/history", response_model=list[HistoryItem])
def history_endpoint() -> list[HistoryItem]:
    return [HistoryItem(**row) for row in get_analysis_history()]


@router.get("/evaluation/summary", response_model=EvaluationSummaryResponse)
def evaluation_summary_endpoint() -> EvaluationSummaryResponse:
    dataset_dir = Path("data/resumes")
    jd_file = Path("data/sample_jd.txt")
    if not jd_file.exists():
        raise HTTPException(status_code=404, detail="Evaluation JD file not found.")
    if not dataset_dir.exists():
        raise HTTPException(status_code=404, detail="Evaluation dataset folder not found.")

    try:
        evaluation = evaluate_dataset(
            dataset_dir=dataset_dir,
            jd_text=jd_file.read_text(encoding="utf-8"),
            threshold=40.0,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate evaluation metrics: {exc}") from exc

    cm = evaluation["confusion_matrix"]
    metrics = evaluation["metrics"]
    auc_score = metrics["auc_score"]
    if isinstance(auc_score, float) and str(auc_score).lower() == "nan":
        auc_score = None

    return EvaluationSummaryResponse(
        threshold=float(evaluation["threshold"]),
        count=int(evaluation["count"]),
        confusion_matrix=[[int(cm[0][0]), int(cm[0][1])], [int(cm[1][0]), int(cm[1][1])]],
        metrics={
            "accuracy": float(metrics["accuracy"]),
            "precision": float(metrics["precision"]),
            "recall": float(metrics["recall"]),
            "f1_score": float(metrics["f1_score"]),
            "sensitivity": float(metrics["sensitivity"]),
            "error_rate": float(metrics["error_rate"]),
            "auc_score": None if auc_score is None else float(auc_score),
        },
        confusion_matrix_image_url="/reports/confusion_matrix.png",
        roc_curve_image_url="/reports/roc_curve.png",
    )

