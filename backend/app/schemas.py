from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    match_score: float = Field(..., ge=0, le=100)
    resume_skills: list[str]
    jd_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    explanation: str


class ResumeLibraryItem(BaseModel):
    resume_name: str
    file_type: str
    last_analyzed_date: str | None = None
    latest_match_score: float | None = None


class HistoryItem(BaseModel):
    id: int
    filename: str
    file_type: str
    match_score: float
    resume_skills: list[str]
    jd_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    explanation: str
    jd_text: str
    timestamp: str


class EvaluationMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    sensitivity: float
    error_rate: float
    auc_score: float | None = None


class EvaluationSummaryResponse(BaseModel):
    threshold: float
    count: int
    confusion_matrix: list[list[int]]
    metrics: EvaluationMetrics
    confusion_matrix_image_url: str
    roc_curve_image_url: str

