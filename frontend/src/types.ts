export type AnalyzeResponse = {
  match_score: number
  resume_skills: string[]
  jd_skills: string[]
  missing_skills: string[]
  suggestions: string[]
  explanation: string
}

export type ResumeLibraryItem = {
  resume_name: string
  file_type: string
  last_analyzed_date: string | null
  latest_match_score: number | null
}

export type HistoryItem = {
  id: number
  filename: string
  file_type: string
  match_score: number
  resume_skills: string[]
  jd_skills: string[]
  missing_skills: string[]
  suggestions: string[]
  explanation: string
  jd_text: string
  timestamp: string
}

export type EvaluationMetrics = {
  accuracy: number
  precision: number
  recall: number
  f1_score: number
  sensitivity: number
  error_rate: number
  auc_score: number | null
}

export type EvaluationSummary = {
  threshold: number
  count: number
  confusion_matrix: [[number, number], [number, number]]
  metrics: EvaluationMetrics
  confusion_matrix_image_url: string
  roc_curve_image_url: string
}

