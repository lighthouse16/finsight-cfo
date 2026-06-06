import {
  AdvisoryBlueprintResponse,
  HardGatePrecheckResult,
  UnifiedRiskScoreResult,
  StressTestingResponse,
  FacilityStructuringResponse,
} from '../types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export async function getAdvisoryBlueprint(): Promise<AdvisoryBlueprintResponse> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-blueprint`, {
    signal: AbortSignal.timeout(8000),
  })
  if (!res.ok) {
    throw new Error(`Blueprint API returned status ${res.status}`)
  }
  return res.json()
}

export async function getAdvisoryPrecheck(): Promise<HardGatePrecheckResult> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-precheck`, {
    signal: AbortSignal.timeout(8000),
  })
  if (!res.ok) {
    throw new Error(`Precheck API returned status ${res.status}`)
  }
  return res.json()
}

export async function getAdvisoryRiskScore(): Promise<UnifiedRiskScoreResult> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-risk-score`, {
    signal: AbortSignal.timeout(8000),
  })
  if (!res.ok) {
    throw new Error(`Risk Score API returned status ${res.status}`)
  }
  return res.json()
}

export async function getAdvisoryStressTests(): Promise<StressTestingResponse> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-stress-tests`, {
    signal: AbortSignal.timeout(8000),
  })
  if (!res.ok) {
    throw new Error(`Stress Tests API returned status ${res.status}`)
  }
  return res.json()
}

export async function getAdvisoryFacilityStructures(): Promise<FacilityStructuringResponse> {
  const res = await fetch(`${API_BASE_URL}/api/advisory/demo-facility-structures`, {
    signal: AbortSignal.timeout(8000),
  })
  if (!res.ok) {
    throw new Error(`Facility Structures API returned status ${res.status}`)
  }
  return res.json()
}
