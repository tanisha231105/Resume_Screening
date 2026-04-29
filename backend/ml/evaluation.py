from __future__ import annotations

from pathlib import Path
from typing import Any
import csv

import matplotlib
import numpy as np
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from ml.dataset_loader import prepare_for_ranking

DEFAULT_THRESHOLD = 40.0
DEFAULT_REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"
DEFAULT_LABELS_FILE = Path(__file__).resolve().parents[1] / "data" / "evaluation_labels.csv"


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _skill_coverage_percent(row: dict[str, Any]) -> float:
    jd_skills = row.get("jd_skills") or []
    missing_skills = row.get("missing_skills") or []
    jd_count = len(jd_skills)
    if jd_count == 0:
        return 0.0
    covered = max(0, jd_count - len(missing_skills))
    return (covered / jd_count) * 100.0


def _build_labels(
    ranked_results: list[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
    labels_file: Path | None = DEFAULT_LABELS_FILE,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build labels without self-referencing the same score for both sides.
    y_true: proxy ground-truth from top/bottom JD skill-coverage ranking
    y_pred: classifier output from ATS match score threshold
    y_score: continuous ATS score for ROC/AUC
    """
    match_scores = np.array([_safe_float(row.get("match_score")) for row in ranked_results], dtype=float)
    filenames = [str(row.get("filename", "")) for row in ranked_results]

    if labels_file is not None and labels_file.exists():
        label_map: dict[str, int] = {}
        with labels_file.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for rec in reader:
                name = (rec.get("filename") or "").strip()
                raw_label = (rec.get("label") or "").strip()
                if not name or raw_label not in {"0", "1"}:
                    continue
                label_map[name] = int(raw_label)

        selected_idx = [i for i, filename in enumerate(filenames) if filename in label_map]
        if len(selected_idx) >= 4:
            y_true = np.array([label_map[filenames[i]] for i in selected_idx], dtype=int)
            if len(np.unique(y_true)) >= 2:
                y_pred = np.array([1 if match_scores[i] >= threshold else 0 for i in selected_idx], dtype=int)
                y_score = np.array([match_scores[i] / 100.0 for i in selected_idx], dtype=float)
                return y_true, y_pred, y_score

    coverage_scores = np.array([_skill_coverage_percent(row) for row in ranked_results], dtype=float)
    n = len(match_scores)
    if n < 4:
        raise ValueError("Need at least 4 ranked samples for stable evaluation.")

    band = max(1, int(n * 0.35))
    sorted_idx = np.argsort(coverage_scores)
    low_idx = sorted_idx[:band]
    high_idx = sorted_idx[-band:]
    eval_idx = np.unique(np.concatenate([low_idx, high_idx]))
    high_idx_set = set(high_idx.tolist())

    y_true = np.array([1 if int(idx) in high_idx_set else 0 for idx in eval_idx], dtype=int)
    y_pred = np.array([1 if match_scores[idx] >= threshold else 0 for idx in eval_idx], dtype=int)
    y_score = np.array([match_scores[idx] / 100.0 for idx in eval_idx], dtype=float)
    return y_true, y_pred, y_score


def generate_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    return confusion_matrix(y_true, y_pred, labels=[0, 1])


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray) -> dict[str, float]:
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    error_rate = 1.0 - accuracy
    sensitivity = recall

    # AUC requires both classes in y_true.
    if len(np.unique(y_true)) < 2:
        auc_score = float("nan")
    else:
        auc_score = roc_auc_score(y_true, y_score)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "sensitivity": sensitivity,
        "error_rate": error_rate,
        "auc_score": auc_score,
    }


def plot_auc_curve(y_true: np.ndarray, y_score: np.ndarray, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))

    if len(np.unique(y_true)) < 2:
        ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="No ROC (single class)")
        ax.set_title("ROC Curve (insufficient class variety)")
    else:
        fpr, tpr, _ = roc_curve(y_true, y_score)
        auc_score = roc_auc_score(y_true, y_score)
        ax.plot(fpr, tpr, label=f"AUC = {auc_score:.3f}", color="#1f77b4", linewidth=2)
        ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random baseline")
        ax.set_title("ROC Curve")

    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def _plot_confusion_matrix(cm: np.ndarray, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Poor Match (0)", "Good Match (1)"])
    display.plot(cmap="Blues", ax=ax, colorbar=False)
    ax.set_title("Confusion Matrix")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def evaluate_ranked_results(
    ranked_results: list[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
    labels_file: Path | None = DEFAULT_LABELS_FILE,
) -> dict[str, Any]:
    if not ranked_results:
        raise ValueError("No ranked results found for evaluation.")

    y_true, y_pred, y_score = _build_labels(ranked_results, threshold=threshold, labels_file=labels_file)
    cm = generate_confusion_matrix(y_true, y_pred)
    metrics = calculate_metrics(y_true, y_pred, y_score)

    cm_path = _plot_confusion_matrix(cm, reports_dir / "confusion_matrix.png")
    roc_path = plot_auc_curve(y_true, y_score, reports_dir / "roc_curve.png")

    return {
        "threshold": threshold,
        "count": len(ranked_results),
        "confusion_matrix": cm,
        "metrics": metrics,
        "confusion_matrix_plot": str(cm_path),
        "roc_curve_plot": str(roc_path),
    }


def evaluate_dataset(
    dataset_dir: str | Path,
    jd_text: str,
    threshold: float = DEFAULT_THRESHOLD,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
    labels_file: Path | None = DEFAULT_LABELS_FILE,
) -> dict[str, Any]:
    ranked = prepare_for_ranking(dataset_dir=dataset_dir, jd_text=jd_text)
    return evaluate_ranked_results(
        ranked_results=ranked,
        threshold=threshold,
        reports_dir=reports_dir,
        labels_file=labels_file,
    )


def format_metrics_report(evaluation: dict[str, Any]) -> str:
    m = evaluation["metrics"]
    cm = evaluation["confusion_matrix"]
    auc_value = m["auc_score"]
    auc_text = f"{auc_value:.2f}" if not np.isnan(auc_value) else "N/A"
    return (
        f"Accuracy: {m['accuracy']*100:.2f}%\n"
        f"Precision: {m['precision']*100:.2f}%\n"
        f"Recall: {m['recall']*100:.2f}%\n"
        f"F1-Score: {m['f1_score']*100:.2f}%\n"
        f"Sensitivity: {m['sensitivity']*100:.2f}%\n"
        f"Error Rate: {m['error_rate']*100:.2f}%\n"
        f"AUC Score: {auc_text}\n\n"
        "Confusion Matrix:\n"
        f"{cm}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run ML evaluation metrics for ranked resumes.")
    parser.add_argument("--dataset-dir", required=True, help="Path to dataset resumes folder")
    parser.add_argument("--jd-file", required=True, help="Path to job description text file")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="Classification threshold percent")
    parser.add_argument(
        "--reports-dir",
        default=str(DEFAULT_REPORTS_DIR),
        help="Directory to save evaluation report images",
    )
    args = parser.parse_args()

    jd_text = Path(args.jd_file).read_text(encoding="utf-8")
    evaluation = evaluate_dataset(
        dataset_dir=args.dataset_dir,
        jd_text=jd_text,
        threshold=args.threshold,
        reports_dir=Path(args.reports_dir),
    )
    print(format_metrics_report(evaluation))
    print(f"\nConfusion Matrix graph: {evaluation['confusion_matrix_plot']}")
    print(f"ROC Curve graph: {evaluation['roc_curve_plot']}")

