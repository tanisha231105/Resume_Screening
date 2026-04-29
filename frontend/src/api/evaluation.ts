import { getApiBaseCandidates } from '@/api/base'
import type { EvaluationSummary } from '@/types'

function joinUrl(base: string, path: string): string {
  return `${base.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`
}

function originFromBase(base: string): string {
  const noSlash = base.replace(/\/+$/, '')
  return noSlash.replace(/\/api$/i, '')
}

export async function fetchEvaluationSummary(signal?: AbortSignal): Promise<EvaluationSummary> {
  let lastStatus: number | undefined
  for (const base of getApiBaseCandidates()) {
    const res = await fetch(`${base}/evaluation/summary`, { signal })
    if (res.ok) {
      const payload = (await res.json()) as EvaluationSummary
      const assetBase = originFromBase(base)
      return {
        ...payload,
        confusion_matrix_image_url: joinUrl(assetBase, payload.confusion_matrix_image_url),
        roc_curve_image_url: joinUrl(assetBase, payload.roc_curve_image_url),
      }
    }
    lastStatus = res.status
    if (res.status !== 404) {
      throw new Error(`Failed to fetch evaluation metrics (${res.status})`)
    }
  }
  throw new Error(`Failed to fetch evaluation metrics (${lastStatus ?? 'network'})`)
}

