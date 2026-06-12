/* eslint-disable @typescript-eslint/no-explicit-any */
import { API_BASE_URL, getWorkspaceHeaders } from './apiBase'

export const RUN_TYPE_SLUGS: Record<string, string> = {
  financial_health: 'financial-health',
  valuation: 'valuation',
  advisory_precheck: 'advisory-precheck',
  credit_score: 'credit-score',
  stress_test: 'stress-test',
  facility_structuring: 'facility-structuring',
  funding_strategy: 'funding-strategy',
  advisory_blueprint: 'advisory-blueprint',
  workflow_run: 'workflow',
}

export interface RunTypeInfo {
  key: string
  label: string
  isCore: boolean
}

export const ANALYSIS_RUN_TYPES: RunTypeInfo[] = [
  { key: 'financial_health', label: 'Financial Health', isCore: true },
  { key: 'valuation', label: 'Valuation', isCore: true },
  { key: 'credit_score', label: 'Credit Readiness', isCore: true },
  { key: 'funding_strategy', label: 'Funding Strategy', isCore: true },
  { key: 'advisory_blueprint', label: 'Advisory Blueprint', isCore: true },
  { key: 'workflow_run', label: 'Workflow Orchestration', isCore: true },
  { key: 'advisory_precheck', label: 'Advisory Precheck', isCore: false },
  { key: 'stress_test', label: 'Stress Testing', isCore: false },
  { key: 'facility_structuring', label: 'Facility Structuring', isCore: false },
]

export function getActiveWorkspaceId(): string | null {
  return localStorage.getItem('active_workspace_id')
}

export async function triggerAnalysisRun(workspaceId: string, runType: string): Promise<any> {
  const slug = RUN_TYPE_SLUGS[runType] || runType
  const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/analysis/${slug}/run`, {
    method: 'POST',
    headers: getWorkspaceHeaders({
      'Content-Type': 'application/json',
    }),
  })
  if (!res.ok) {
    const errorDetail = await res.json().then((d) => d.detail ?? res.statusText).catch(() => res.statusText)
    throw new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail))
  }
  return res.json()
}

export async function fetchLatestRunSafe(workspaceId: string, runType: string): Promise<any | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/runs/latest?type=${runType}`, {
      headers: getWorkspaceHeaders(),
    })
    if (!res.ok) {
      return null
    }
    return await res.json()
  } catch (error) {
    console.warn(`Failed to fetch latest run safe for ${runType}:`, error)
    return null
  }
}

export async function fetchAllRunStatuses(workspaceId: string): Promise<Record<string, any | null>> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/workspaces/${workspaceId}/runs`, {
      headers: getWorkspaceHeaders(),
    })
    if (!res.ok) {
      return {}
    }
    const runs = await res.json()
    const statuses: Record<string, any | null> = {}
    
    // Initialize all to null
    for (const typeInfo of ANALYSIS_RUN_TYPES) {
      statuses[typeInfo.key] = null
    }
    
    // Since list_runs returns sorted by createdAt descending, the first one we find is the latest
    for (const run of runs) {
      const runType = run.runType
      if (runType && statuses[runType] === null) {
        statuses[runType] = run
      }
    }
    
    return statuses
  } catch (error) {
    console.error('Failed to fetch all run statuses:', error)
    return {}
  }
}

export function isRunMissing(run: any): boolean {
  return !run
}

export function getRunStatusLabel(run: any): 'completed' | 'failed' | 'not run' {
  if (!run) return 'not run'
  if (run.status === 'completed' || run.status === 'success') return 'completed'
  if (run.status === 'failed') return 'failed'
  return 'not run'
}

export interface BackendConfig {
  appMode: string
  allowDemoFallback: boolean
  isProduction: boolean
}

const SAFE_BACKEND_CONFIG: BackendConfig = {
  appMode: 'production',
  allowDemoFallback: false,
  isProduction: true,
}

export async function fetchBackendConfig(): Promise<BackendConfig> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/workspaces/config`)
    if (!res.ok) {
      return SAFE_BACKEND_CONFIG
    }
    const data = await res.json()
    const appMode = data.app_mode ?? 'production'
    const allowDemoFallback = data.allow_demo_fallback ?? false
    const isProduction = appMode === 'production' || !allowDemoFallback
    return { appMode, allowDemoFallback, isProduction }
  } catch (e) {
    console.warn('Failed to fetch backend config, using production-safe defaults:', e)
    return SAFE_BACKEND_CONFIG
  }
}
