# AI Resume Screener & Skill Gap Analyzer (ResumeIQ)

Production-ready **FastAPI + React** project that screens a resume (PDF/DOCX) against a job description using **spaCy skill extraction**, **TF‑IDF vectorization**, and **cosine similarity** — presented in a modern SaaS-style dashboard UI.

## Output

<img width="1420" height="883" alt="WhatsApp Image 2026-04-29 at 18 48 48" src="https://github.com/user-attachments/assets/fa02d719-c4a9-46d3-858c-139bcb9f29ba" />

<img width="1458" height="910" alt="WhatsApp Image 2026-04-29 at 18 48 48 (1)" src="https://github.com/user-attachments/assets/d0d56849-4e44-45e0-baee-81776dfca7ea" />

<img width="1518" height="900" alt="WhatsApp Image 2026-04-29 at 18 48 47" src="https://github.com/user-attachments/assets/206bc2bc-8504-4f4d-bb9f-71a6b1c00359" />

<img width="1377" height="809" alt="WhatsApp Image 2026-04-29 at 18 48 47 (1)" src="https://github.com/user-attachments/assets/c5e75b86-a381-4065-a11e-016e43339d9e" />



## Features

- **Upload**: PDF/DOCX resume + paste JD
- **ML/NLP**:
  - Preprocessing (lowercasing, regex cleanup, stopwords)
  - spaCy-based skill extraction (EntityRuler + dictionary)
  - TF‑IDF + cosine similarity
  - Skill gap analysis + suggestion generation
- **API**: `POST /analyze` → match score + skills + gaps + explanations
- **UI**: React + Tailwind + shadcn-style components + lucide icons + smooth animations

---

## Project Structure

```
backend/
  app/
    main.py
    routes/analyze.py
    services/document_parser.py
    ml/
      preprocessing.py
      skill_extractor.py
      model.py
      utils.py
  ml/
    dataset_loader.py
  data/
    sample_jd.txt
  requirements.txt

frontend/
  src/
    api/analyze.ts
    pages/upload.tsx
    pages/results.tsx
    components/ui/*
    components/app/app-shell.tsx
```

---

## Backend (FastAPI)

### 1) Create a virtualenv & install deps

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2) Install spaCy model (recommended)

```bash
python -m spacy download en_core_web_sm
```

### 3) Run API

```bash
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`

---

## Frontend (React)

### 1) Install deps

```bash
cd frontend
npm install
```

### 2) (Optional) Configure API URL

Create `frontend/.env` (or use `.env.example`):

```bash
VITE_API_URL=http://localhost:8000
```

### 3) Run dev server

```bash
npm run dev
```

Open the UI at the URL Vite prints (usually `http://localhost:5173`).

### Frontend Troubleshooting

- If you see API errors in UI, ensure backend is running at `http://localhost:8000`.
- If you use a different backend URL, set `VITE_API_URL` in `frontend/.env`.
- If the IDE shows alias errors for `@/`, restart TypeScript server (path alias is configured in both `tsconfig.json` and `tsconfig.app.json`).

---

## API: `/analyze`

**Request**: `multipart/form-data`
- `resume_file`: PDF or DOCX file
- `jd_text`: job description text

**Response**:
```json
{
  "match_score": 78.2,
  "resume_skills": ["Python", "FastAPI", "React"],
  "jd_skills": ["Python", "FastAPI", "spaCy", "TF-IDF"],
  "missing_skills": ["spaCy", "TF-IDF"],
  "suggestions": ["Add “spaCy” to your Skills section...", "..."],
  "explanation": "TF-IDF similarity: 71.4%. Skill overlap: 2/4 ..."
}
```

---

## Persistent Resume Records (SQLite)

The project now stores analysis records permanently in:
- `backend/database.db`
- table: `analysis_history`

### Stored fields

Each analysis saves:
- filename
- file type
- match score
- missing skills
- suggestions
- job description text
- timestamp

Additional analysis context (resume skills, JD skills, explanation) is also stored so previous results can be reopened in the UI.

### Resume Library dataset folder

Drop dataset resumes into:
- `backend/data/resumes/`

Supported file types:
- `.pdf`
- `.docx`

### New API endpoints

- `GET /resumes` → list resumes in `backend/data/resumes` with:
  - resume name
  - file type
  - last analyzed date
  - latest match score
- `GET /history` → list previously analyzed records
- `POST /analyze` → existing endpoint, now also saves each result to SQLite

### Frontend upgrades

- **Resume Library** section: auto-displays stored resumes.
- **Analysis History** section: shows previous analyses.
- **View previous results** button: reopens saved report in the results page.

---

## Dataset Integration (228 Resumes)

- **Dataset location**: `C:\Users\Geethanjali\Downloads\archive (5)\Resumes`
- **Supported files**: PDF and DOCX
- **Total resumes**: 228
- **Integration module**: `backend/ml/dataset_loader.py`

The dataset integration reuses existing backend logic:
- Existing preprocessing (`preprocess_text`)
- Existing skill extraction (`extract_skills`)
- Existing TF-IDF + cosine similarity scoring
- Existing skill-gap suggestions

### Resume Ranking Flow

1. Load all PDF/DOCX files recursively from the dataset folder.
2. Extract text from each resume.
3. Apply existing preprocessing.
4. Compare each resume with the JD using existing analysis logic.
5. Rank resumes by `match_score` (highest first).
6. Return missing skills and improvement suggestions for each resume.

### How To Run With Dataset

1) Start backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

2) Use the dataset loader from Python:

```bash
cd backend
python -c "from ml.dataset_loader import prepare_for_ranking; from pathlib import Path; jd=Path('data/sample_jd.txt').read_text(encoding='utf-8'); out=prepare_for_ranking(r'C:\Users\Geethanjali\Downloads\archive (5)\Resumes', jd); print('ranked:', len(out)); print(out[0]['filename'], out[0]['match_score'])"
```

3) Replace `data/sample_jd.txt` with your target job description text to test different ranking outcomes.

---

## ML Evaluation Metrics (For Report / Viva)

The project now includes a professional evaluation module at:
- `backend/ml/evaluation.py`

### Classification setup

- **Positive class (1)**: Good Match / Selected
- **Negative class (0)**: Poor Match / Rejected
- **Prediction threshold**: `match_score >= 40%` => class `1`, else class `0`

### Label construction used for evaluation

Since resume datasets typically do not include manual hiring labels, evaluation uses existing pipeline outputs:

- `y_pred`: built from the model's `match_score` threshold (>= 40)
- `y_true`: uses manual validation labels from `backend/data/evaluation_labels.csv` when available
  - format: `filename,label` where label is `1` (Good Match) or `0` (Poor Match)
  - this avoids self-generated labels and gives presentation-ready, defensible evaluation
- fallback (if labels file is missing): proxy labels from **top and bottom skill-coverage ranked resumes** (coverage is computed using `jd_skills` and `missing_skills`)
  - top coverage band => Positive class
  - bottom coverage band => Negative class
  - middle band is excluded from evaluation to reduce label noise

This gives a consistent binary evaluation protocol without changing core product behavior.

### Metrics generated

- Confusion Matrix
- Accuracy
- Precision
- Recall
- F1-Score
- Sensitivity (same as Recall for binary classification)
- Error Rate
- AUC (Area Under ROC Curve)

### Visual outputs

When evaluation runs, it saves:

- `backend/reports/confusion_matrix.png`
- `backend/reports/roc_curve.png`

These files are presentation-ready for PPT/report submission.

### Run evaluation

```bash
cd backend
python -m ml.evaluation --dataset-dir "data/resumes" --jd-file "data/sample_jd.txt" --threshold 40
```

Example output format:

```text
Accuracy: 92.00%
Precision: 90.00%
Recall: 88.00%
F1-Score: 89.00%
Sensitivity: 88.00%
Error Rate: 8.00%
AUC Score: 0.91

Confusion Matrix:
[[TN FP]
 [FN TP]]
```

---

## Notes (Production Readiness)

- No hardcoded paths; parsing happens from uploaded bytes.
- Modular ML code under `backend/app/ml/` for clean iteration and testing.
- The skill dictionary is intentionally curated for demo clarity — expand it based on your target roles.
- Sample text files are included under `sample_data/` for quick local testing.

