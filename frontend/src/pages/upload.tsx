import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  Clock3,
  FileText,
  FolderOpen,
  History,
  UploadCloud,
  Wand2,
  AlertCircle,
} from 'lucide-react'

import { analyzeResume } from '@/api/analyze'
import { fetchAnalysisHistory, fetchResumeLibrary } from '@/api/records'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Spinner } from '@/components/ui/spinner'
import type { AnalyzeResponse, HistoryItem, ResumeLibraryItem } from '@/types'

const SAMPLE_JD = `We are hiring a Full-Stack Engineer with strong ML/NLP fundamentals.

Must have:
- Python, FastAPI
- React + TypeScript
- NLP: spaCy, TF-IDF, cosine similarity
- Data: pandas, numpy

Nice to have:
- Docker, CI/CD
- AWS (S3/Lambda)
- Observability (logging, metrics)`

export function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [jdText, setJdText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [library, setLibrary] = useState<ResumeLibraryItem[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [isLoadingRecords, setIsLoadingRecords] = useState(true)
  const [recordsError, setRecordsError] = useState<string | null>(null)

  const inputRef = useRef<HTMLInputElement | null>(null)

  const fileMeta = useMemo(() => {
    if (!file) return null
    const mb = (file.size / (1024 * 1024)).toFixed(2)
    return `${file.name} · ${mb} MB`
  }, [file])

  useEffect(() => {
    const controller = new AbortController()

    async function loadRecords() {
      setIsLoadingRecords(true)
      setRecordsError(null)
      try {
        const [libraryRows, historyRows] = await Promise.all([
          fetchResumeLibrary(controller.signal),
          fetchAnalysisHistory(controller.signal),
        ])
        setLibrary(libraryRows)
        setHistory(historyRows)
      } catch (e) {
        if (controller.signal.aborted) return
        setRecordsError(e instanceof Error ? e.message : 'Failed to load stored records.')
      } finally {
        if (!controller.signal.aborted) setIsLoadingRecords(false)
      }
    }

    void loadRecords()
    return () => controller.abort()
  }, [])

  function openHistoryResult(item: HistoryItem) {
    const result: AnalyzeResponse = {
      match_score: item.match_score,
      resume_skills: item.resume_skills,
      jd_skills: item.jd_skills,
      missing_skills: item.missing_skills,
      suggestions: item.suggestions,
      explanation: item.explanation,
    }
    navigate('/results', { state: { result, jdText: item.jd_text } })
  }

  async function onAnalyze() {
    if (!file) {
      setError('Please upload a PDF or DOCX resume.')
      return
    }
    if (!jdText.trim()) {
      setError('Please paste a job description.')
      return
    }

    setError(null)
    setIsLoading(true)
    try {
      const result = await analyzeResume({ file, jdText })
      navigate('/results', { state: { result, jdText } })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="grid place-items-center">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="w-full max-w-4xl"
      >
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground shadow-sm">
            <Wand2 className="h-3.5 w-3.5" />
            Production-ready ML · SaaS-style UI
          </div>
          <h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
            AI Resume Screener & Skill Gap Analyzer
          </h1>
          <p className="mt-2 text-balance text-sm text-muted-foreground sm:text-base">
            Upload a resume (PDF/DOCX), paste a job description, and get an ATS
            match score with missing skills and concrete suggestions.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="group relative overflow-hidden">
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UploadCloud className="h-5 w-5 text-muted-foreground" />
                Resume upload
              </CardTitle>
              <CardDescription>
                PDF or DOCX. We extract text and screen it against the JD.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input
                ref={inputRef}
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />

              <div className="flex items-center justify-between gap-3 rounded-md border bg-muted/30 px-3 py-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  <span className="truncate">
                    {fileMeta ?? 'No file selected'}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => inputRef.current?.click()}
                >
                  Browse
                </Button>
              </div>

              <div className="text-xs text-muted-foreground">
                Tip: Use a clean, single-column resume for best ATS parsing.
              </div>
            </CardContent>
          </Card>

          <Card className="group relative overflow-hidden">
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-muted-foreground" />
                Job description
              </CardTitle>
              <CardDescription>
                Paste the role requirements. We extract skills and compute
                similarity.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the job description here..."
                className="min-h-[220px] resize-none"
              />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setJdText(SAMPLE_JD)}
                >
                  Use sample JD
                </Button>
                <div className="text-xs text-muted-foreground">
                  {jdText.trim().length.toLocaleString()} chars
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 flex flex-col items-center gap-3">
          {error && (
            <div className="flex w-full max-w-4xl items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4" />
              <div className="leading-relaxed">{error}</div>
            </div>
          )}

          <Button
            onClick={onAnalyze}
            size="lg"
            className="w-full max-w-sm shadow-sm transition-transform duration-200 hover:-translate-y-0.5"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Spinner className="h-4 w-4" />
                Analyzing…
              </>
            ) : (
              <>
                Analyze resume
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
          <div className="text-xs text-muted-foreground">
            Your files are processed locally by the backend API you run.
          </div>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderOpen className="h-5 w-5 text-muted-foreground" />
                Resume Library
              </CardTitle>
              <CardDescription>
                Auto-discovered resumes from <code>backend/data/resumes</code>.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoadingRecords ? (
                <div className="text-sm text-muted-foreground">Loading library…</div>
              ) : recordsError ? (
                <div className="text-sm text-destructive">{recordsError}</div>
              ) : library.length === 0 ? (
                <div className="text-sm text-muted-foreground">
                  No resumes found. Add PDF/DOCX files to <code>backend/data/resumes</code>.
                </div>
              ) : (
                library.map((item) => (
                  <div
                    key={item.resume_name}
                    className="rounded-lg border bg-muted/20 px-3 py-2 text-sm"
                  >
                    <div className="font-medium">{item.resume_name}</div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="secondary">{item.file_type.toUpperCase()}</Badge>
                      <span>
                        Last analyzed:{' '}
                        {item.last_analyzed_date
                          ? new Date(item.last_analyzed_date).toLocaleString()
                          : 'Never'}
                      </span>
                      <span>
                        Latest score:{' '}
                        {item.latest_match_score !== null ? item.latest_match_score : 'N/A'}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5 text-muted-foreground" />
                Analysis History
              </CardTitle>
              <CardDescription>
                Previously analyzed results stored in SQLite.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoadingRecords ? (
                <div className="text-sm text-muted-foreground">Loading history…</div>
              ) : recordsError ? (
                <div className="text-sm text-destructive">{recordsError}</div>
              ) : history.length === 0 ? (
                <div className="text-sm text-muted-foreground">
                  No analysis history yet. Run an analysis to create records.
                </div>
              ) : (
                history.slice(0, 12).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start justify-between gap-3 rounded-lg border bg-muted/20 px-3 py-2"
                  >
                    <div className="min-w-0 text-sm">
                      <div className="truncate font-medium">{item.filename}</div>
                      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock3 className="h-3.5 w-3.5" />
                        {new Date(item.timestamp).toLocaleString()}
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        Score: {item.match_score}
                      </div>
                    </div>
                    <Button size="sm" variant="outline" onClick={() => openHistoryResult(item)}>
                      View previous results
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </div>
  )
}

