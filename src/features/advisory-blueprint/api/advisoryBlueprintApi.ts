import {
  AdvisoryBlueprintResponse,
  HardGatePrecheckResult,
  UnifiedRiskScoreResult,
  CreditScoringResult,
  StressTestingResponse,
  FacilityStructuringResponse,
} from '../types'
import type { FinancialAnalysisResponse } from '../../market-watch/types'

import { API_BASE_URL, getWorkspaceHeaders, handleApiResponse } from '../../../lib/apiBase'


export async function getAdvisoryBlueprint(): Promise<AdvisoryBlueprintResponse> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-blueprint`, {
    headers: getWorkspaceHeaders(),
    signal: AbortSignal.timeout(8000),
  })
  return handleApiResponse(res)
}

export async function getAdvisoryPrecheck(): Promise<HardGatePrecheckResult> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-precheck`, {
    headers: getWorkspaceHeaders(),
    signal: AbortSignal.timeout(8000),
  })
  return handleApiResponse(res)
}

export async function getAdvisoryRiskScore(): Promise<UnifiedRiskScoreResult> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-risk-score`, {
    headers: getWorkspaceHeaders(),
    signal: AbortSignal.timeout(8000),
  })
  return handleApiResponse(res)
}

export async function getCreditScore(): Promise<CreditScoringResult> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/credit-score`, {
    headers: getWorkspaceHeaders(),
    signal: AbortSignal.timeout(8000),
  })
  return handleApiResponse(res)
}

export async function getAdvisoryStressTests(): Promise<StressTestingResponse> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-stress-tests`, {
    headers: getWorkspaceHeaders(),
    signal: AbortSignal.timeout(8000),
  })
  return handleApiResponse(res)
}

export async function getAdvisoryFacilityStructures(): Promise<FacilityStructuringResponse> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-facility-structures`, {
    headers: getWorkspaceHeaders(),
    signal: AbortSignal.timeout(8000),
  })
  return handleApiResponse(res)
}

export async function getFinancialPreviewAnalysis(): Promise<FinancialAnalysisResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/financials/preview-analysis`, {
      headers: getWorkspaceHeaders(),
      signal: AbortSignal.timeout(5000),
    })
    if (res.status === 404) {
      return null
    }
    if (!res.ok) {
      throw new Error(`Preview analysis API returned status ${res.status}`)
    }
    return res.json()
  } catch (error) {
    console.warn('Financial preview analysis fetch failed; keeping advisory blueprint context', error)
    return null
  }
}
