import type { FinancialAnalysisResponse } from '../market-watch/types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export async function getFinancialHealthAnalysis(): Promise<FinancialAnalysisResponse> {
  try {
    const previewRes = await fetch(`${API_BASE_URL}/api/financials/preview-analysis`, {
      signal: AbortSignal.timeout(5000),
    })

    if (previewRes.ok) {
      return previewRes.json()
    }

    if (previewRes.status !== 404) {
      console.warn(`Preview financial analysis returned ${previewRes.status}; falling back to demo analysis.`)
    }
  } catch (error) {
    console.warn('Preview financial analysis unavailable; falling back to demo analysis.', error)
  }

  const demoRes = await fetch(`${API_BASE_URL}/api/financials/demo-analysis`, {
    signal: AbortSignal.timeout(8000),
  })

  if (!demoRes.ok) {
    throw new Error(`Financial analysis API returned status ${demoRes.status}`)
  }

  return demoRes.json()
}
