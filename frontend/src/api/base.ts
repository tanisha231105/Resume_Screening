function normalizeBase(url: string): string {
  return url.trim().replace(/\/+$/, '')
}

function configuredBase(): string {
  const envUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? ''
  return normalizeBase(envUrl) || 'http://localhost:8000'
}

export function getApiBaseCandidates(): string[] {
  const base = configuredBase()
  const withoutApi = normalizeBase(base.replace(/\/api$/i, ''))
  const withApi = normalizeBase(`${withoutApi}/api`)

  // Windows local setups often have backend on 8001 when 8000 is occupied.
  const localFallbacks = [
    'http://127.0.0.1:8001',
    'http://localhost:8001',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
  ]

  return Array.from(
    new Set(
      [base, withoutApi, withApi, ...localFallbacks]
        .map(normalizeBase)
        .flatMap((candidate) => [candidate, normalizeBase(`${candidate}/api`)]),
    ),
  )
}

