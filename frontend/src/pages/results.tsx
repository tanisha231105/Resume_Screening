import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  BadgeCheck,
  BrainCircuit,
  ClipboardList,
  Sparkles,
  TrendingUp,
  Wrench,
} from 'lucide-react'

import type { AnalyzeResponse } from '@/types'
import type { EvaluationSummary } from '@/types'
import { fetchEvaluationSummary } from '@/api/evaluation'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'

type LocationState = { result: AnalyzeResponse; jdText?: string }

function scoreLabel(score: number) {
  if (score >= 80) return { label: 'Excellent match', tone: 'text-emerald-600' }
  if (score >= 60) return { label: 'Good match', tone: 'text-sky-600' }
  if (score >= 40) return { label: 'Moderate match', tone: 'text-amber-600' }
  return { label: 'Low match', tone: 'text-red-600' }
}

export function ResultsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null

  useEffect(() => {
    if (!state?.result) navigate('/', { replace: true })
  }, [navigate, state?.result])

  const result = state?.result
  const score = useMemo(() => (result ? Math.round(result.match_score) : 0), [result])
  const meta = scoreLabel(score)
  const [evaluation, setEvaluation] = useState<EvaluationSummary | null>(null)
  const [evaluationError, setEvaluationError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    async function loadEvaluation() {
      try {
        setEvaluationError(null)
        const summary = await fetchEvaluationSummary(controller.signal)
        if (!controller.signal.aborted) setEvaluation(summary)
      } catch (e) {
        if (controller.signal.aborted) return
        setEvaluationError(e instanceof Error ? e.message : 'Failed to load evaluation metrics.')
      }
    }
    void loadEvaluation()
    return () => controller.abort()
  }, [])

  if (!result) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="space-y-6"
    >
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground shadow-sm">
            <Sparkles className="h-3.5 w-3.5" />
            Results dashboard
          </div>
          <h2 className="text-2xl font-semibold tracking-tight">
            ATS Match & Skill Gap Report
          </h2>
          <p className="text-sm text-muted-foreground">
            Skills extracted from your resume and the job description, plus actionable next steps.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button asChild variant="outline">
            <Link to="/" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              New analysis
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-muted-foreground" />
              ATS Score
            </CardTitle>
            <CardDescription>
              Computed using TF-IDF cosine similarity + skill coverage.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-end justify-between gap-4">
              <div className="space-y-1">
                <div className="text-4xl font-semibold tracking-tight">
                  {score}
                  <span className="text-base text-muted-foreground">/100</span>
                </div>
                <div className={`text-sm font-medium ${meta.tone}`}>{meta.label}</div>
              </div>
              <div className="rounded-lg border bg-muted/20 px-4 py-3 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <BadgeCheck className="h-4 w-4" />
                  <span>
                    Resume skills: <span className="text-foreground">{result.resume_skills.length}</span>
                  </span>
                </div>
                <div className="mt-1 flex items-center gap-2 text-muted-foreground">
                  <ClipboardList className="h-4 w-4" />
                  <span>
                    JD skills: <span className="text-foreground">{result.jd_skills.length}</span>
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Low</span>
                <span>High</span>
              </div>
              <Progress value={score} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wrench className="h-5 w-5 text-muted-foreground" />
              Missing skills
            </CardTitle>
            <CardDescription>
              Skills in the JD that didn’t appear in your resume.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {result.missing_skills.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No gaps detected — strong alignment.
              </div>
            ) : (
              result.missing_skills.map((s) => (
                <Badge key={s} variant="danger">
                  {s}
                </Badge>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="group">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BadgeCheck className="h-5 w-5 text-muted-foreground" />
              Resume skills
            </CardTitle>
            <CardDescription>
              Extracted via spaCy pipeline + curated skill dictionary.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {result.resume_skills.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No skills extracted — try a cleaner resume format or add a skills section.
              </div>
            ) : (
              result.resume_skills.map((s) => (
                <Badge key={s} variant="success">
                  {s}
                </Badge>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="group">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-muted-foreground" />
              JD skills
            </CardTitle>
            <CardDescription>
              What the job is explicitly asking for.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {result.jd_skills.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No skills extracted — the JD may be too short or generic.
              </div>
            ) : (
              result.jd_skills.map((s) => (
                <Badge key={s} variant="secondary">
                  {s}
                </Badge>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BrainCircuit className="h-5 w-5 text-muted-foreground" />
              Suggestions
            </CardTitle>
            <CardDescription>
              Concrete changes to close gaps and improve ATS alignment.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {result.suggestions.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No suggestions generated.
              </div>
            ) : (
              <ul className="space-y-2 text-sm">
                {result.suggestions.map((s, idx) => (
                  <li
                    key={`${idx}-${s}`}
                    className="rounded-lg border bg-muted/20 px-3 py-2 leading-relaxed transition-colors hover:bg-muted/30"
                  >
                    {s}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-muted-foreground" />
              Explanation
            </CardTitle>
            <CardDescription>
              What influenced the score and where the gaps are.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border bg-muted/20 px-4 py-3 text-sm leading-relaxed">
              {result.explanation}
            </div>

            <Separator />

            <div className="text-xs text-muted-foreground">
              Tip: If a missing skill is real, add it under “Skills”, and reinforce with a bullet in your most relevant project.
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-muted-foreground" />
            Model Evaluation Dashboard
          </CardTitle>
          <CardDescription>
            Dataset-level model evaluation for presentation/report (threshold: 40% selected vs rejected).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {evaluationError ? (
            <div className="text-sm text-destructive">{evaluationError}</div>
          ) : !evaluation ? (
            <div className="text-sm text-muted-foreground">Loading evaluation metrics...</div>
          ) : (
            <>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <div className="rounded-lg border bg-muted/20 px-3 py-2">
                  <div className="text-xs text-muted-foreground">Accuracy</div>
                  <div className="text-lg font-semibold">{(evaluation.metrics.accuracy * 100).toFixed(2)}%</div>
                </div>
                <div className="rounded-lg border bg-muted/20 px-3 py-2">
                  <div className="text-xs text-muted-foreground">Precision</div>
                  <div className="text-lg font-semibold">{(evaluation.metrics.precision * 100).toFixed(2)}%</div>
                </div>
                <div className="rounded-lg border bg-muted/20 px-3 py-2">
                  <div className="text-xs text-muted-foreground">Recall</div>
                  <div className="text-lg font-semibold">{(evaluation.metrics.recall * 100).toFixed(2)}%</div>
                </div>
                <div className="rounded-lg border bg-muted/20 px-3 py-2">
                  <div className="text-xs text-muted-foreground">F1 Score</div>
                  <div className="text-lg font-semibold">{(evaluation.metrics.f1_score * 100).toFixed(2)}%</div>
                </div>
                <div className="rounded-lg border bg-muted/20 px-3 py-2">
                  <div className="text-xs text-muted-foreground">AUC</div>
                  <div className="text-lg font-semibold">
                    {evaluation.metrics.auc_score === null ? 'N/A' : evaluation.metrics.auc_score.toFixed(2)}
                  </div>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="space-y-2">
                  <div className="text-sm font-medium">Confusion Matrix</div>
                  <img
                    src={evaluation.confusion_matrix_image_url}
                    alt="Confusion Matrix"
                    className="w-full rounded-lg border bg-white object-contain"
                    loading="lazy"
                  />
                </div>
                <div className="space-y-2">
                  <div className="text-sm font-medium">ROC Curve</div>
                  <img
                    src={evaluation.roc_curve_image_url}
                    alt="ROC Curve"
                    className="w-full rounded-lg border bg-white object-contain"
                    loading="lazy"
                  />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

