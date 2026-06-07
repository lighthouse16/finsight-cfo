export interface WorkspaceSnapshotPreviewSummary {
  integrityPassedCount: number
  integrityWarningCount: number
  integrityFailedCount: number
  ratioKeys: string[]
}

export interface WorkspaceAnalysisContext {
  source: 'data_room_preview'
  activatedAt: string
  companyName: string
  reportingPeriod: string
  currency: string
  snapshotPreviewSummary: WorkspaceSnapshotPreviewSummary
  disclaimer: string
}

const WORKSPACE_ANALYSIS_CONTEXT_KEY = 'finsight:workspace-analysis-context:v1'

const canUseLocalStorage = () => {
  try {
    return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
  } catch {
    return false
  }
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const isSummary = (value: unknown): value is WorkspaceSnapshotPreviewSummary => {
  if (!isRecord(value)) return false
  return (
    typeof value.integrityPassedCount === 'number' &&
    typeof value.integrityWarningCount === 'number' &&
    typeof value.integrityFailedCount === 'number' &&
    Array.isArray(value.ratioKeys) &&
    value.ratioKeys.every((ratioKey) => typeof ratioKey === 'string')
  )
}

const isWorkspaceAnalysisContext = (value: unknown): value is WorkspaceAnalysisContext => {
  if (!isRecord(value)) return false
  return (
    value.source === 'data_room_preview' &&
    typeof value.activatedAt === 'string' &&
    typeof value.companyName === 'string' &&
    typeof value.reportingPeriod === 'string' &&
    typeof value.currency === 'string' &&
    isSummary(value.snapshotPreviewSummary) &&
    typeof value.disclaimer === 'string'
  )
}

export function loadWorkspaceAnalysisContext(): WorkspaceAnalysisContext | null {
  if (!canUseLocalStorage()) return null

  try {
    const rawValue = window.localStorage.getItem(WORKSPACE_ANALYSIS_CONTEXT_KEY)
    if (!rawValue) return null

    const parsed = JSON.parse(rawValue) as unknown
    return isWorkspaceAnalysisContext(parsed) ? parsed : null
  } catch {
    return null
  }
}

export function saveWorkspaceAnalysisContext(context: WorkspaceAnalysisContext) {
  if (!canUseLocalStorage()) return

  try {
    window.localStorage.setItem(WORKSPACE_ANALYSIS_CONTEXT_KEY, JSON.stringify(context))
  } catch {
    // Ignore localStorage quota/security failures; workspace context remains page-local.
  }
}

export function clearWorkspaceAnalysisContext() {
  if (!canUseLocalStorage()) return

  try {
    window.localStorage.removeItem(WORKSPACE_ANALYSIS_CONTEXT_KEY)
  } catch {
    // Ignore localStorage security failures.
  }
}

export function hasActiveWorkspaceAnalysisContext() {
  return loadWorkspaceAnalysisContext() !== null
}

export { WORKSPACE_ANALYSIS_CONTEXT_KEY }
