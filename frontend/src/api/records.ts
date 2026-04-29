import type { HistoryItem, ResumeLibraryItem } from '@/types'
import { getApiBaseCandidates } from '@/api/base'

export async function fetchResumeLibrary(signal?: AbortSignal): Promise<ResumeLibraryItem[]> {
  let lastStatus: number | undefined
  for (const base of getApiBaseCandidates()) {
    const res = await fetch(`${base}/resumes`, { signal })
    if (res.ok) return (await res.json()) as ResumeLibraryItem[]
    lastStatus = res.status
    if (res.status !== 404) {
      throw new Error(`Failed to fetch resume library (${res.status})`)
    }
  }
  throw new Error(`Failed to fetch resume library (${lastStatus ?? 'network'})`)
}

export async function fetchAnalysisHistory(signal?: AbortSignal): Promise<HistoryItem[]> {
  let lastStatus: number | undefined
  for (const base of getApiBaseCandidates()) {
    const res = await fetch(`${base}/history`, { signal })
    if (res.ok) return (await res.json()) as HistoryItem[]
    lastStatus = res.status
    if (res.status !== 404) {
      throw new Error(`Failed to fetch analysis history (${res.status})`)
    }
  }
  throw new Error(`Failed to fetch analysis history (${lastStatus ?? 'network'})`)
}
