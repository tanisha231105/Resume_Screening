import type { AnalyzeResponse } from '@/types'
import { getApiBaseCandidates } from '@/api/base'

export async function analyzeResume(args: {
  file: File
  jdText: string
  signal?: AbortSignal
}): Promise<AnalyzeResponse> {
  const fd = new FormData()
  fd.append('resume_file', args.file)
  fd.append('jd_text', args.jdText)

  let lastStatus: number | undefined
  let lastMessage = ''
  for (const base of getApiBaseCandidates()) {
    const res = await fetch(`${base}/analyze`, {
      method: 'POST',
      body: fd,
      signal: args.signal,
    })

    if (res.ok) {
      return (await res.json()) as AnalyzeResponse
    }

    const text = await res.text().catch(() => '')
    let message = text
    try {
      const parsed = JSON.parse(text) as { detail?: string }
      if (parsed?.detail) message = parsed.detail
    } catch {
      // keep text fallback
    }

    lastStatus = res.status
    lastMessage = message
    if (res.status !== 404) {
      throw new Error(message || `Request failed (${res.status})`)
    }
  }

  throw new Error(lastMessage || `Request failed (${lastStatus ?? 'network'})`)
}

